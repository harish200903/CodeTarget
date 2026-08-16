import uuid
import time
import hashlib
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user, get_ai_service
from app.models.user import User
from app.models.problem import Problem
from app.models.submission import Submission, UserProblemProgress, ProgressStatus
from app.models.user_ai_hint import UserAIHint
from app.models.ai_log import AIUsageLog
from app.schemas.ai import (
    AIHintRequest,
    AIHintResponse,
    UserAIHintItem,
    UserAIHintHistoryResponse,
)
from app.services.ai.base import AIService
from app.services.ai.limiter import check_ai_rate_limit
from app.services.ai.cache import AICacheService, generate_ai_cache_key
from app.services.ai.exceptions import (
    AIServiceError,
    AIConfigurationError,
    AIRateLimitExceeded,
    AIProviderTimeout,
    AIProviderUnavailable,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{problem_id}", response_model=UserAIHintHistoryResponse)
async def get_user_ai_hints_history(
    problem_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves authenticated user's unlocked AI hint history for a specific problem."""
    stmt = (
        select(UserAIHint)
        .where(
            UserAIHint.user_id == current_user.id,
            UserAIHint.problem_id == problem_id,
        )
        .order_by(UserAIHint.hint_level.asc())
    )
    result = await db.execute(stmt)
    hints = result.scalars().all()

    return UserAIHintHistoryResponse(
        items=[UserAIHintItem.model_validate(h) for h in hints],
        hints_unlocked=len(hints),
        max_hints=3,
    )


@router.post("", response_model=AIHintResponse)
async def request_ai_hint(
    payload: AIHintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    ai_service: AIService = Depends(get_ai_service),
):
    """Generates the next progressive AI hint for candidate code draft."""
    # 1. Validate Problem existence
    stmt = select(Problem).where(Problem.id == payload.problem_id)
    res = await db.execute(stmt)
    problem = res.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found.",
        )

    # 2. Check if user has already SOLVED this problem
    progress_stmt = select(UserProblemProgress).where(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.problem_id == payload.problem_id,
    )
    progress_res = await db.execute(progress_stmt)
    user_progress = progress_res.scalar_one_or_none()

    if user_progress and user_progress.status == ProgressStatus.SOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already solved this problem! Review your approach or optimize your code instead of requesting hints.",
        )

    # 3. Determine next progressive hint level (0 -> Level 1, 1 -> Level 2, 2 -> Level 3, 3+ -> Reject)
    existing_hints_stmt = (
        select(UserAIHint)
        .where(
            UserAIHint.user_id == current_user.id,
            UserAIHint.problem_id == payload.problem_id,
        )
        .order_by(UserAIHint.hint_level.asc())
    )
    existing_res = await db.execute(existing_hints_stmt)
    existing_hints = existing_res.scalars().all()
    unlocked_count = len(existing_hints)

    if unlocked_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have used all 3 AI hints for this problem.",
        )

    next_hint_level = unlocked_count + 1

    # 4. Global Redis Rate Limiting Check
    try:
        await check_ai_rate_limit(current_user.id, redis)
    except AIRateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
        )

    # 5. Calculate source code hash & Check Cache Strategy
    code_text = payload.source_code or ""
    code_hash = hashlib.sha256(code_text.encode("utf-8")).hexdigest()
    cache_payload = {
        "problem_id": str(payload.problem_id),
        "hint_level": next_hint_level,
        "language": payload.language,
        "code_hash": code_hash,
    }
    cache_key = generate_ai_cache_key("hint", cache_payload, user_id=str(current_user.id))
    cache_service = AICacheService(redis_client=redis)
    cached_data = await cache_service.get(cache_key)

    if cached_data:
        logger.info(f"AI Hint Cache HIT for user {current_user.id}, problem {payload.problem_id}, level {next_hint_level}")
        return AIHintResponse(**cached_data)

    # 6. Execute AI Service Call with Latency & Usage Tracking
    start_time = time.time()
    cache_hit = False
    is_success = True
    error_msg = None

    try:
        hint_response = await ai_service.generate_hint(
            problem_title=problem.title,
            difficulty=problem.difficulty.value,
            description=problem.description_markdown,
            constraints=problem.constraints_text or "",
            user_code=code_text,
            language=payload.language,
            hint_level=next_hint_level,
        )
        # Ensure returned hint level strictly matches next_hint_level
        hint_response.hint_level = next_hint_level

    except AIConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI hint service is currently disabled or missing configuration.",
        )
    except AIProviderTimeout as e:
        is_success = False
        error_msg = "Provider timeout"
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Generating the hint took too long. Please try again shortly.",
        )
    except (AIProviderUnavailable, AIServiceError) as e:
        is_success = False
        error_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Your AI mentor is temporarily unavailable. Please try again shortly.",
        )
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        # Log AI Usage to DB
        usage_log = AIUsageLog(
            user_id=current_user.id,
            operation="HINT",
            model_name="gemini-2.5-flash",
            prompt_version="v1",
            latency_ms=latency_ms,
            is_success=is_success,
            error_message=error_msg,
            cache_hit=cache_hit,
        )
        db.add(usage_log)

    # 7. Persist UserAIHint Record to DB
    new_user_hint = UserAIHint(
        user_id=current_user.id,
        problem_id=payload.problem_id,
        hint_level=next_hint_level,
        language=payload.language,
        source_code_hash=code_hash,
        hint_text=hint_response.hint_text,
        focus_concept=hint_response.focus_concept,
        should_reveal_solution=hint_response.should_reveal_solution,
    )
    db.add(new_user_hint)
    await db.commit()

    # 8. Store in Redis Cache for instant refresh
    await cache_service.set(cache_key, hint_response.model_dump())

    return hint_response

import uuid
import time
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user, get_ai_service
from app.models.user import User
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.user_ai_code_review import UserAICodeReview
from app.models.ai_log import AIUsageLog
from app.schemas.ai import (
    AICodeReviewRequest,
    AICodeReviewResponse,
    UserAICodeReviewDetailResponse,
)
from app.services.ai.base import AIService
from app.services.ai.limiter import check_ai_rate_limit
from app.services.ai.exceptions import (
    AIServiceError,
    AIConfigurationError,
    AIRateLimitExceeded,
    AIProviderTimeout,
    AIProviderUnavailable,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{problem_id}", response_model=Optional[UserAICodeReviewDetailResponse])
async def get_latest_user_ai_code_review(
    problem_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves candidate's latest AI code review for a specific problem."""
    stmt = (
        select(UserAICodeReview)
        .where(
            UserAICodeReview.user_id == current_user.id,
            UserAICodeReview.problem_id == problem_id,
        )
        .order_by(UserAICodeReview.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        return None

    return UserAICodeReviewDetailResponse.model_validate(review)


@router.post("", response_model=AICodeReviewResponse)
async def request_ai_code_review(
    payload: AICodeReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    ai_service: AIService = Depends(get_ai_service),
):
    """Generates an AI-powered code review for candidate source code."""
    # 1. Validate empty / whitespace code
    if not payload.source_code or not payload.source_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter some source code before requesting an AI code review.",
        )

    # 2. Validate Problem existence
    stmt = select(Problem).where(Problem.id == payload.problem_id)
    res = await db.execute(stmt)
    problem = res.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found.",
        )

    # 3. Global Redis Rate Limiting Check
    try:
        await check_ai_rate_limit(current_user.id, redis)
    except AIRateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=e.message,
        )

    # 4. Enforce Product-Level Rate Limit: Max 3 code reviews per problem per hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_reviews_stmt = select(UserAICodeReview).where(
        UserAICodeReview.user_id == current_user.id,
        UserAICodeReview.problem_id == payload.problem_id,
        UserAICodeReview.created_at >= one_hour_ago,
    )
    recent_res = await db.execute(recent_reviews_stmt)
    recent_count = len(recent_res.scalars().all())

    if recent_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have reached your limit of 3 AI code reviews per problem per hour. Try refining your code or running test cases.",
        )

    # 5. Fetch safe Judge0 submission context (if candidate submitted code previously)
    latest_sub_stmt = (
        select(Submission)
        .where(
            Submission.user_id == current_user.id,
            Submission.problem_id == payload.problem_id,
        )
        .order_by(Submission.created_at.desc())
        .limit(1)
    )
    sub_res = await db.execute(latest_sub_stmt)
    latest_sub = sub_res.scalar_one_or_none()
    judge0_status_text = latest_sub.status if latest_sub else None

    # 6. Execute AI Service Code Review Call
    start_time = time.time()
    is_success = True
    error_msg = None

    try:
        review_response = await ai_service.review_code(
            problem_title=problem.title,
            difficulty=problem.difficulty.value,
            description=problem.description_markdown,
            user_code=payload.source_code,
            language=payload.language,
        )
        review_response.judge0_status = judge0_status_text

    except AIConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI code review service is currently disabled or missing configuration.",
        )
    except AIProviderTimeout as e:
        is_success = False
        error_msg = "Provider timeout"
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Code review took too long. Please try again shortly.",
        )
    except (AIProviderUnavailable, AIServiceError) as e:
        is_success = False
        error_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Your AI reviewer is temporarily unavailable. Please try again shortly.",
        )
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        # Log AI Usage
        usage_log = AIUsageLog(
            user_id=current_user.id,
            operation="CODE_REVIEW",
            model_name="gemini-2.5-flash",
            prompt_version="v1",
            latency_ms=latency_ms,
            is_success=is_success,
            error_message=error_msg,
            cache_hit=False,
        )
        db.add(usage_log)

    # 7. Persist UserAICodeReview to DB
    code_hash = hashlib.sha256(payload.source_code.encode("utf-8")).hexdigest()
    new_review = UserAICodeReview(
        user_id=current_user.id,
        problem_id=payload.problem_id,
        language=payload.language,
        source_code_hash=code_hash,
        summary=review_response.summary,
        correctness_assessment=review_response.correctness_assessment,
        time_complexity=review_response.time_complexity,
        space_complexity=review_response.space_complexity,
        strengths=review_response.strengths,
        improvements=review_response.improvements,
        bugs=review_response.bugs,
        suggestions=review_response.suggestions,
        judge0_status=judge0_status_text,
    )
    db.add(new_review)
    await db.commit()

    return review_response

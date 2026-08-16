import logging
import math
import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, or_

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user
from app.models.user import User
from app.models.problem import Problem, TestCase
from app.models.submission import Submission, UserProblemProgress, SubmissionStatus, ProgressStatus
from app.schemas.submission import (
    RunSampleRequest,
    SubmitSolutionRequest,
    SubmissionOut,
    SubmissionPaginatedResponse
)
from app.services.execution import get_execution_service, ExecutionService, BatchExecutionResult
from app.services.gamification import GamificationService

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_rate_limit(user_id: uuid.UUID, redis_client) -> None:
    """Rate limits submissions to 10 per minute per user using Redis sliding window."""
    if not redis_client:
        return
    try:
        key = f"rate_limit:submission:{user_id}"
        now = time.time()
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, now - 60)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, 65)
        res = await pipe.execute()
        count = res[1]
        if count >= 10:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. You can submit up to 10 solutions per minute."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Redis rate limit check skipped due to connection issue: {e}")


@router.post("/run-sample", response_model=BatchExecutionResult)
async def run_sample_code(
    body: RunSampleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """Dry-run code against public sample test cases without persisting a permanent submission."""
    stmt = select(Problem).where(Problem.id == body.problem_id)
    res = await db.execute(stmt)
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    tc_stmt = select(TestCase).where(and_(TestCase.problem_id == body.problem_id, TestCase.is_sample == True))
    tc_res = await db.execute(tc_stmt)
    sample_cases = tc_res.scalars().all()

    if not sample_cases:
        all_tc_stmt = select(TestCase).where(TestCase.problem_id == body.problem_id)
        all_tc_res = await db.execute(all_tc_stmt)
        sample_cases = all_tc_res.scalars().all()

    formatted_test_cases = [
        {"input_data": tc.input_data, "expected_output": tc.expected_output}
        for tc in sample_cases
    ]

    return await execution_service.run_sample_test_cases(
        language=body.language,
        source_code=body.code,
        test_cases=formatted_test_cases
    )


@router.post("/submit", response_model=SubmissionOut)
async def submit_solution(
    body: SubmitSolutionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """Submit code solution against hidden evaluation test cases and update progress & gamification."""
    if redis_client:
        await check_rate_limit(current_user.id, redis_client)

    stmt = select(Problem).where(Problem.id == body.problem_id)
    res = await db.execute(stmt)
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    tc_stmt = select(TestCase).where(TestCase.problem_id == body.problem_id)
    tc_res = await db.execute(tc_stmt)
    test_cases = tc_res.scalars().all()

    formatted_test_cases = [
        {"input_data": tc.input_data, "expected_output": tc.expected_output}
        for tc in test_cases
    ]

    exec_result = await execution_service.execute_submission(
        language=body.language,
        source_code=body.code,
        test_cases=formatted_test_cases
    )

    submission = Submission(
        user_id=current_user.id,
        problem_id=body.problem_id,
        language=body.language,
        code=body.code,
        status=exec_result.overall_status,
        execution_time_ms=exec_result.execution_time_ms,
        memory_kb=exec_result.memory_kb,
        passed_test_cases=exec_result.passed_test_cases,
        total_test_cases=exec_result.total_test_cases,
        error_output=exec_result.error_output
    )
    db.add(submission)
    await db.flush()

    prog_stmt = select(UserProblemProgress).where(
        and_(
            UserProblemProgress.user_id == current_user.id,
            UserProblemProgress.problem_id == body.problem_id
        )
    )
    prog_res = await db.execute(prog_stmt)
    user_prog = prog_res.scalar_one_or_none()

    prev_status = user_prog.status if user_prog else ProgressStatus.UNATTEMPTED

    if not user_prog:
        user_prog = UserProblemProgress(
            user_id=current_user.id,
            problem_id=body.problem_id,
            status=ProgressStatus.SOLVED if exec_result.overall_status == SubmissionStatus.ACCEPTED else ProgressStatus.ATTEMPTED,
            attempts_count=1
        )
        db.add(user_prog)
    else:
        user_prog.attempts_count += 1
        if exec_result.overall_status == SubmissionStatus.ACCEPTED:
            user_prog.status = ProgressStatus.SOLVED
        elif user_prog.status == ProgressStatus.UNATTEMPTED:
            user_prog.status = ProgressStatus.ATTEMPTED

    await db.commit()
    await db.refresh(submission)

    # Process Gamification (XP, Level, Streak, Badges)
    if exec_result.overall_status == SubmissionStatus.ACCEPTED:
        try:
            is_first_solve = (prev_status != ProgressStatus.SOLVED)
            await GamificationService.process_problem_solve(
                db=db,
                user_id=current_user.id,
                problem=problem,
                is_first_solve=is_first_solve
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to process gamification solve: {e}")

    # Invalidate cache
    if redis_client:
        try:
            keys = await redis_client.keys(f"recommendations:user:{current_user.id}:*")
            prep_keys = await redis_client.keys(f"company_prep:user:{current_user.id}:*")
            all_keys = list(keys) + list(prep_keys)
            if all_keys:
                await redis_client.delete(*all_keys)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")

    return submission


@router.get("/problem/{problem_id}", response_model=SubmissionPaginatedResponse)
async def get_user_submissions_for_problem(
    problem_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve paginated submission history for the authenticated user and specific problem."""
    base_query = select(Submission).where(
        and_(
            Submission.user_id == current_user.id,
            Submission.problem_id == problem_id
        )
    )

    count_query = select(func.count(Submission.id)).where(
        and_(
            Submission.user_id == current_user.id,
            Submission.problem_id == problem_id
        )
    )
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    query = base_query.order_by(Submission.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(query)
    submissions = res.scalars().all()

    return SubmissionPaginatedResponse(
        items=submissions,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )

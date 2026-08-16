import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.deps import get_current_user, get_ai_service
from app.models.user import User
from app.models.problem import Problem, TestCase
from app.schemas.mock_test import (
    MockTestCatalogItem,
    UserMockTestSessionResponse,
    SubmitMockProblemRequest,
    SubmitMockProblemResponse,
    MockTestResultResponse,
    MockTestHistoryItem,
)
from app.services.mock_test import MockTestService
from app.services.execution import get_execution_service, ExecutionService, BatchExecutionResult
from app.services.ai.base import AIService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[MockTestCatalogItem])
async def list_available_mock_tests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists available mock company tests matching candidate's selected target companies."""
    service = MockTestService(db=db)
    return await service.get_catalog(user=current_user)


@router.post("/{mock_test_id}/start", response_model=UserMockTestSessionResponse)
async def start_mock_test_session(
    mock_test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Starts a new mock test session or resumes an active in-progress session."""
    service = MockTestService(db=db)
    return await service.start_mock_test(user=current_user, mock_test_id=mock_test_id)


@router.get("/sessions/{session_id}", response_model=UserMockTestSessionResponse)
async def get_active_mock_test_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves active mock test session details and recalculates remaining time server-side."""
    service = MockTestService(db=db)
    return await service.get_session(user=current_user, session_id=session_id)


@router.post("/sessions/{session_id}/problems/{problem_id}/run-sample", response_model=BatchExecutionResult)
async def run_mock_problem_sample(
    session_id: uuid.UUID,
    problem_id: uuid.UUID,
    body: SubmitMockProblemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    execution_service: ExecutionService = Depends(get_execution_service),
):
    """Dry-runs candidate code against public sample test cases during an active mock test."""
    service = MockTestService(db=db)
    # Ensure active session validity
    await service.get_session(user=current_user, session_id=session_id)

    # Fetch public sample test cases
    tc_stmt = select(TestCase).where(TestCase.problem_id == problem_id, TestCase.is_sample == True)
    tc_res = await db.execute(tc_stmt)
    sample_cases = tc_res.scalars().all()

    if not sample_cases:
        all_tc_stmt = select(TestCase).where(TestCase.problem_id == problem_id)
        all_tc_res = await db.execute(all_tc_stmt)
        sample_cases = all_tc_res.scalars().all()

    formatted_test_cases = [
        {"input_data": tc.input_data, "expected_output": tc.expected_output}
        for tc in sample_cases
    ]

    return await execution_service.run_sample_test_cases(
        language=body.language,
        source_code=body.code,
        test_cases=formatted_test_cases,
    )


@router.post("/sessions/{session_id}/problems/{problem_id}/submit", response_model=SubmitMockProblemResponse)
async def submit_mock_problem_solution(
    session_id: uuid.UUID,
    problem_id: uuid.UUID,
    body: SubmitMockProblemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    execution_service: ExecutionService = Depends(get_execution_service),
):
    """Submits problem solution against hidden test cases during an active timed mock test."""
    service = MockTestService(db=db)
    return await service.submit_problem_solution(
        user=current_user,
        session_id=session_id,
        problem_id=problem_id,
        language=body.language,
        code=body.code,
        execution_service=execution_service,
    )


@router.post("/sessions/{session_id}/submit", response_model=MockTestResultResponse)
async def submit_complete_mock_test(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalizes and evaluates complete mock test session."""
    service = MockTestService(db=db)
    return await service.submit_mock_test(user=current_user, session_id=session_id)


@router.get("/sessions/{session_id}/result", response_model=MockTestResultResponse)
async def get_mock_test_result(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
):
    """Retrieves score card, topic breakdown, and recommendations for a completed mock test."""
    service = MockTestService(db=db, ai_service=ai_service)
    return await service.get_mock_test_result(user=current_user, session_id=session_id)


@router.get("/history", response_model=List[MockTestHistoryItem])
async def get_mock_test_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves candidate history of completed mock tests."""
    service = MockTestService(db=db)
    return await service.get_user_history(user=current_user)

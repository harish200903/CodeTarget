import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MockTestProblemItem(BaseModel):
    problem_id: uuid.UUID
    title: str
    slug: str
    difficulty: str
    category: str
    order_index: int
    weight_score: int
    user_status: str = "UNATTEMPTED"  # UNATTEMPTED, ATTEMPTED, SOLVED
    score_obtained: int = 0
    code_draft: Optional[str] = None


class MockTestCatalogItem(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    company_slug: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    problem_count: int
    total_points: int
    user_last_status: Optional[str] = None
    user_last_score: Optional[int] = None

    class Config:
        from_attributes = True


class UserMockTestSessionResponse(BaseModel):
    session_id: uuid.UUID
    mock_test_id: uuid.UUID
    title: str
    company_name: str
    company_slug: str
    duration_minutes: int
    started_at: datetime
    expires_at: datetime
    remaining_seconds: int
    status: str
    total_score: int
    max_possible_score: int
    problems: List[MockTestProblemItem]


class SubmitMockProblemRequest(BaseModel):
    language: str
    code: str


class SubmitMockProblemResponse(BaseModel):
    submission_id: uuid.UUID
    status: str
    passed_test_cases: int
    total_test_cases: int
    score_obtained: int
    execution_time_ms: Optional[float] = None
    memory_kb: Optional[float] = None
    error_output: Optional[str] = None


class MockTestResultProblemDetail(BaseModel):
    problem_id: uuid.UUID
    title: str
    slug: str
    difficulty: str
    order_index: int
    weight_score: int
    score_obtained: int
    status: str  # ACCEPTED, WRONG_ANSWER, UNATTEMPTED, etc.
    passed_test_cases: int
    total_test_cases: int


class MockTestTopicPerformance(BaseModel):
    topic_id: uuid.UUID
    topic_name: str
    problems_count: int
    solved_count: int
    status: str  # STRONG, NEEDS_PRACTICE


class MockTestDifficultyPerformance(BaseModel):
    difficulty: str
    problems_count: int
    solved_count: int


class MockTestResultResponse(BaseModel):
    session_id: uuid.UUID
    mock_test_id: uuid.UUID
    title: str
    company_name: str
    status: str
    score: int
    total_points: int
    percentage: float
    time_taken_seconds: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    problems: List[MockTestResultProblemDetail]
    topic_breakdown: List[MockTestTopicPerformance]
    difficulty_breakdown: List[MockTestDifficultyPerformance]
    recommended_next_steps: List[str]
    ai_explanation: Optional[str] = None


class MockTestHistoryItem(BaseModel):
    session_id: uuid.UUID
    mock_test_id: uuid.UUID
    title: str
    company_name: str
    company_slug: str
    status: str
    score: int
    total_points: int
    percentage: float
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

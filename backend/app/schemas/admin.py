import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AdminDashboardSummary(BaseModel):
    companies_count: int
    topics_count: int
    problems_count: int
    active_problems_count: int
    mock_tests_count: int
    total_test_cases: int
    total_hints: int


class AdminCompanyCreateRequest(BaseModel):
    name: str
    slug: str
    tier: str = "Service"
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = True


class AdminCompanyUpdateRequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    tier: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class AdminTopicCreateRequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True


class AdminTopicUpdateRequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AdminProblemCreateRequest(BaseModel):
    title: str
    slug: str
    difficulty: str  # EASY, MEDIUM, HARD
    category: str
    description_markdown: str
    constraints_text: Optional[str] = None
    starter_code: Dict[str, str] = Field(default_factory=dict)
    solution_editorial: Optional[str] = None
    is_active: bool = True
    company_ids: List[uuid.UUID] = Field(default_factory=list)
    topic_ids: List[uuid.UUID] = Field(default_factory=list)


class AdminProblemUpdateRequest(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    description_markdown: Optional[str] = None
    constraints_text: Optional[str] = None
    starter_code: Optional[Dict[str, str]] = None
    solution_editorial: Optional[str] = None
    is_active: Optional[bool] = None
    company_ids: Optional[List[uuid.UUID]] = None
    topic_ids: Optional[List[uuid.UUID]] = None


class AdminTestCaseCreateRequest(BaseModel):
    input_data: str
    expected_output: str
    is_sample: bool = False
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256


class AdminTestCaseUpdateRequest(BaseModel):
    input_data: Optional[str] = None
    expected_output: Optional[str] = None
    is_sample: Optional[bool] = None
    time_limit_ms: Optional[int] = None
    memory_limit_mb: Optional[int] = None


class AdminHintCreateRequest(BaseModel):
    step_number: int
    title: str
    content_markdown: str


class AdminHintUpdateRequest(BaseModel):
    step_number: Optional[int] = None
    title: Optional[str] = None
    content_markdown: Optional[str] = None


class MockTestProblemAssignment(BaseModel):
    problem_id: uuid.UUID
    order_index: int
    weight_score: int = 100


class AdminMockTestCreateRequest(BaseModel):
    company_id: uuid.UUID
    title: str
    description: Optional[str] = None
    duration_minutes: int = 60
    problem_assignments: List[MockTestProblemAssignment] = Field(default_factory=list)


class AdminMockTestUpdateRequest(BaseModel):
    company_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    problem_assignments: Optional[List[MockTestProblemAssignment]] = None


class AuditLogItem(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogPaginatedResponse(BaseModel):
    items: List[AuditLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int

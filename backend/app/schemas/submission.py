import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.submission import SubmissionStatus


class RunSampleRequest(BaseModel):
    problem_id: uuid.UUID
    language: str = Field(..., description="Programming language: python, java, or cpp")
    code: str = Field(..., min_length=1, max_length=65536, description="Source code")


class SubmitSolutionRequest(BaseModel):
    problem_id: uuid.UUID
    language: str = Field(..., description="Programming language: python, java, or cpp")
    code: str = Field(..., min_length=1, max_length=65536, description="Source code")


class SubmissionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    problem_id: uuid.UUID
    language: str
    code: str
    status: SubmissionStatus
    execution_time_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    passed_test_cases: int
    total_test_cases: int
    error_output: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionPaginatedResponse(BaseModel):
    items: List[SubmissionOut]
    page: int
    page_size: int
    total: int
    total_pages: int

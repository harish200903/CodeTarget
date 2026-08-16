import uuid
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.problem import DifficultyLevel, InterviewRoundType
from app.models.company import SourceClassification
from app.models.submission import ProgressStatus
from app.schemas.company import CompanyOut


class TopicOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProblemCompanyOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company: CompanyOut
    frequency_weight: float
    recency_window: str
    round_type: InterviewRoundType
    source_classification: SourceClassification

    model_config = ConfigDict(from_attributes=True)


class TestCaseOut(BaseModel):
    id: uuid.UUID
    input_data: str
    expected_output: str
    is_sample: bool

    model_config = ConfigDict(from_attributes=True)


class HintOut(BaseModel):
    id: uuid.UUID
    step_number: int
    title: str
    content_markdown: str
    code_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProblemListItemOut(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    difficulty: DifficultyLevel
    category: str
    topics: List[TopicOut] = []
    companies: List[ProblemCompanyOut] = []
    user_status: ProgressStatus = ProgressStatus.UNATTEMPTED
    is_bookmarked: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProblemDetailOut(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    description_markdown: str
    difficulty: DifficultyLevel
    category: str
    constraints_text: Optional[str] = None
    starter_code: Dict[str, str]
    topics: List[TopicOut] = []
    companies: List[ProblemCompanyOut] = []
    sample_test_cases: List[TestCaseOut] = []
    user_status: ProgressStatus = ProgressStatus.UNATTEMPTED
    hints_unlocked: int = 0
    hints: List[HintOut] = []  # Only unlocked hints
    is_bookmarked: bool = False
    personal_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProblemPaginatedResponse(BaseModel):
    items: List[ProblemListItemOut]
    page: int
    page_size: int
    total: int
    total_pages: int


class BookmarkRequest(BaseModel):
    is_bookmarked: bool


class NotesRequest(BaseModel):
    personal_notes: str = Field(..., max_length=5000)

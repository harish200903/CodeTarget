import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CompanyInfo(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class TopicBreakdownItem(BaseModel):
    topic_id: uuid.UUID
    topic_name: str
    available: int
    attempted: int
    solved: int
    solve_rate: float
    coverage_pct: float
    status: str = Field(..., description="Topic status (NOT_STARTED, NEEDS_PRACTICE, DEVELOPING, STRONG)")

    model_config = ConfigDict(from_attributes=True)


class DifficultyBreakdownItem(BaseModel):
    difficulty: str = Field(..., description="Difficulty level (EASY, MEDIUM, HARD)")
    available: int
    attempted: int
    solved: int
    solve_rate: float

    model_config = ConfigDict(from_attributes=True)


class CoverageMetrics(BaseModel):
    overall: float
    topics: float
    difficulty: float

    model_config = ConfigDict(from_attributes=True)


class ProblemCounts(BaseModel):
    available: int
    attempted: int
    solved: int

    model_config = ConfigDict(from_attributes=True)


class CompanyPreparationResponse(BaseModel):
    company: CompanyInfo
    preparation_score: Optional[int] = Field(None, ge=0, le=100, description="CodeTarget preparation coverage score (0-100)")
    status: str = Field(..., description="Preparation state (INSUFFICIENT_DATA, STARTING, DEVELOPING, WELL_PREPARED)")
    confidence_message: str = Field(..., description="User-facing status summary")
    coverage: CoverageMetrics
    problems: ProblemCounts
    topic_breakdown: List[TopicBreakdownItem]
    difficulty_breakdown: List[DifficultyBreakdownItem]
    strengths: List[str]
    focus_areas: List[str]
    recommended_next_steps: List[str]
    ai_explanation: Optional[str] = Field(None, description="Optional concise AI-generated explanation")

    model_config = ConfigDict(from_attributes=True)

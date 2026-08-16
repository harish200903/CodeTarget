import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.problem import ProblemListItemOut


class AIHintRequest(BaseModel):
    problem_id: uuid.UUID = Field(..., description="Target problem UUID")
    language: str = Field("python", description="Programming language context")
    source_code: Optional[str] = Field("", description="Current candidate code draft")


class AICodeReviewRequest(BaseModel):
    problem_id: uuid.UUID = Field(..., description="Target problem UUID")
    language: str = Field("python", description="Programming language context")
    source_code: str = Field(..., description="Current candidate code draft")


class UserAIHintItem(BaseModel):
    id: uuid.UUID
    hint_level: int
    language: str
    hint_text: str
    focus_concept: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAIHintHistoryResponse(BaseModel):
    items: List[UserAIHintItem]
    hints_unlocked: int
    max_hints: int = 3


class AIHintResponse(BaseModel):
    hint_text: str = Field(..., description="Progressive hint guidance for candidate")
    hint_level: int = Field(..., ge=1, le=3, description="Hint step level (1, 2, or 3)")
    should_reveal_solution: bool = Field(False, description="Whether full solution should be revealed")
    focus_concept: Optional[str] = Field(None, description="Core algorithmic concept focused by hint")

    model_config = ConfigDict(from_attributes=True)


class AICodeReviewResponse(BaseModel):
    summary: str = Field(..., description="High-level overview of submitted code solution")
    correctness_assessment: str = Field(..., description="Assessment of logical correctness and edge cases")
    time_complexity: str = Field(..., description="Estimated asymptotic Big-O time complexity")
    space_complexity: str = Field(..., description="Estimated asymptotic Big-O space complexity")
    strengths: List[str] = Field(default_factory=list, description="Notable strengths of code solution")
    improvements: List[str] = Field(default_factory=list, description="Recommended optimization areas")
    bugs: List[str] = Field(default_factory=list, description="Identified logical or edge-case bugs")
    suggestions: List[str] = Field(default_factory=list, description="Actionable refactoring suggestions")
    judge0_status: Optional[str] = Field(None, description="Associated Judge0 execution result if available")

    model_config = ConfigDict(from_attributes=True)


class UserAICodeReviewDetailResponse(BaseModel):
    id: uuid.UUID
    problem_id: uuid.UUID
    language: str
    summary: str
    correctness_assessment: str
    time_complexity: str
    space_complexity: str
    strengths: List[str]
    improvements: List[str]
    bugs: List[str]
    suggestions: List[str]
    judge0_status: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIErrorExplanationResponse(BaseModel):
    error_type: str = Field(..., description="Category of error (Syntax, Runtime, TLE, Logic)")
    explanation: str = Field(..., description="Clear explanation of root cause")
    suggested_direction: str = Field(..., description="Suggested approach to resolve error")
    key_line_number: Optional[int] = Field(None, description="Line number associated with error if applicable")

    model_config = ConfigDict(from_attributes=True)


class AIRecommendationResponse(BaseModel):
    reasoning: str = Field(..., description="Explanation for recommended practice problems")
    recommended_problem_ids: List[str] = Field(default_factory=list, description="Target problem IDs")
    focus_topics: List[str] = Field(default_factory=list, description="DSA topic areas needing reinforcement")

    model_config = ConfigDict(from_attributes=True)


class RecommendationItem(BaseModel):
    problem: ProblemListItemOut
    reason: str = Field(..., description="Human-readable reason for recommendation")
    reason_type: str = Field(..., description="Categorized reason code (WEAK_TOPIC, COMPANY_PREPARATION, DIFFICULTY_PROGRESSION, REINFORCEMENT, CHALLENGE)")
    score: int = Field(..., description="Internal recommendation score (0-100)")

    model_config = ConfigDict(from_attributes=True)


class RecommendationListResponse(BaseModel):
    items: List[RecommendationItem]
    focus_topics: List[str]
    source: str = Field("ai", description="Recommendation engine source ('ai' or 'deterministic')")

    model_config = ConfigDict(from_attributes=True)

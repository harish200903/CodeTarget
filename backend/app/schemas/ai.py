from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


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

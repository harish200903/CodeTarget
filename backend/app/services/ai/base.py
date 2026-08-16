from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.ai import (
    AIHintResponse,
    AICodeReviewResponse,
    AIErrorExplanationResponse,
    AIRecommendationResponse,
)


class AIService(ABC):
    """Abstract Base Class defining provider-independent AI capabilities."""

    @abstractmethod
    async def generate_hint(
        self,
        problem_title: str,
        difficulty: str,
        description: str,
        constraints: str,
        user_code: str,
        language: str,
        hint_level: int,
    ) -> AIHintResponse:
        pass

    @abstractmethod
    async def review_code(
        self,
        problem_title: str,
        difficulty: str,
        description: str,
        user_code: str,
        language: str,
    ) -> AICodeReviewResponse:
        pass

    @abstractmethod
    async def explain_error(
        self,
        user_code: str,
        language: str,
        error_output: str,
    ) -> AIErrorExplanationResponse:
        pass

    @abstractmethod
    async def generate_recommendation(
        self,
        target_companies: List[str],
        skill_level: str,
        weak_topics: List[str],
        available_problems: List[Dict[str, Any]],
    ) -> AIRecommendationResponse:
        pass

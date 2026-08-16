import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from app.core.config import settings
from app.services.ai.base import AIService
from app.services.ai.exceptions import (
    AIConfigurationError,
    AIProviderUnavailable,
    AIProviderTimeout,
    AIResponseValidationError,
)
from app.schemas.ai import (
    AIHintResponse,
    AICodeReviewResponse,
    AIErrorExplanationResponse,
    AIRecommendationResponse,
)
from app.services.ai.prompts.templates import (
    HINT_SYSTEM_PROMPT,
    HINT_USER_TEMPLATE,
    CODE_REVIEW_SYSTEM_PROMPT,
    CODE_REVIEW_USER_TEMPLATE,
    ERROR_EXPLANATION_SYSTEM_PROMPT,
    ERROR_EXPLANATION_USER_TEMPLATE,
    RECOMMENDATION_SYSTEM_PROMPT,
    RECOMMENDATION_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)


class GeminiAIService(AIService):
    """Google Gemini 2.5 Flash concrete provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.ai_enabled = settings.AI_ENABLED
        self.timeout = settings.AI_REQUEST_TIMEOUT_SECONDS
        self.max_input_chars = settings.AI_MAX_INPUT_CHARS

        # Lazy initialized Google GenAI Client
        self._client = None

    def _get_client(self):
        """Initializes and returns the official Google GenAI Client if enabled and configured."""
        if not self.ai_enabled:
            raise AIConfigurationError("AI subsystem is disabled in environment configuration (AI_ENABLED=false).")

        if not self.api_key:
            raise AIConfigurationError("Google Gemini API key is not configured (GEMINI_API_KEY is empty).")

        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                # Fallback check if google-genai / google-generativeai SDK is loaded
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.api_key)
                    self._client = genai.GenerativeModel(self.model_name)
                except Exception as e:
                    logger.error(f"Failed to initialize Google GenAI SDK: {e}")
                    raise AIProviderUnavailable("Failed to initialize Google Gemini AI client SDK.")
            except Exception as e:
                logger.error(f"Google GenAI Client initialization error: {e}")
                raise AIProviderUnavailable("Failed to connect to Google Gemini AI service.")

        return self._client

    def _truncate_input(self, text: str) -> str:
        """Safely truncates long inputs to fit configured limits."""
        if not text:
            return ""
        return text[: self.max_input_chars]

    async def _generate_content_with_timeout(self, system_prompt: str, user_prompt: str) -> str:
        """Executes Gemini model generation with timeout protection."""
        client = self._get_client()

        async def _call_gemini():
            # Support both google.genai and google.generativeai interface styles
            if hasattr(client, "models"):
                # google.genai style
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config={
                        "system_instruction": system_prompt,
                        "response_mime_type": "application/json",
                    }
                )
                return response.text
            elif hasattr(client, "generate_content"):
                # google.generativeai style
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = client.generate_content(full_prompt)
                return response.text
            else:
                raise AIProviderUnavailable("Unrecognized Gemini API client interface.")

        try:
            return await asyncio.wait_for(_call_gemini(), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.error(f"Gemini API request timed out after {self.timeout} seconds.")
            raise AIProviderTimeout(f"Gemini API request timed out after {self.timeout} seconds.")
        except Exception as e:
            logger.error(f"Gemini API execution error: {e}")
            raise AIProviderUnavailable(f"Google Gemini service error: {str(e)}")

    def _parse_json_response(self, raw_text: str) -> dict:
        """Parses and cleans JSON string output from model."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output from Gemini model: {e}. Raw text: {raw_text[:200]}")
            raise AIResponseValidationError("AI model returned malformed non-JSON output.")

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
        user_prompt = HINT_USER_TEMPLATE.format(
            hint_level=hint_level,
            problem_title=problem_title,
            difficulty=difficulty,
            description=self._truncate_input(description),
            constraints=self._truncate_input(constraints),
            language=language,
            user_code=self._truncate_input(user_code),
        )

        raw_json_str = await self._generate_content_with_timeout(HINT_SYSTEM_PROMPT, user_prompt)
        parsed_dict = self._parse_json_response(raw_json_str)

        try:
            return AIHintResponse(**parsed_dict)
        except ValidationError as e:
            logger.error(f"AIHintResponse schema validation failed: {e}")
            raise AIResponseValidationError(f"Invalid hint schema: {e}")

    async def review_code(
        self,
        problem_title: str,
        difficulty: str,
        description: str,
        user_code: str,
        language: str,
    ) -> AICodeReviewResponse:
        user_prompt = CODE_REVIEW_USER_TEMPLATE.format(
            problem_title=problem_title,
            difficulty=difficulty,
            description=self._truncate_input(description),
            language=language,
            user_code=self._truncate_input(user_code),
        )

        raw_json_str = await self._generate_content_with_timeout(CODE_REVIEW_SYSTEM_PROMPT, user_prompt)
        parsed_dict = self._parse_json_response(raw_json_str)

        try:
            return AICodeReviewResponse(**parsed_dict)
        except ValidationError as e:
            logger.error(f"AICodeReviewResponse schema validation failed: {e}")
            raise AIResponseValidationError(f"Invalid code review schema: {e}")

    async def explain_error(
        self,
        user_code: str,
        language: str,
        error_output: str,
    ) -> AIErrorExplanationResponse:
        user_prompt = ERROR_EXPLANATION_USER_TEMPLATE.format(
            language=language,
            user_code=self._truncate_input(user_code),
            error_output=self._truncate_input(error_output),
        )

        raw_json_str = await self._generate_content_with_timeout(ERROR_EXPLANATION_SYSTEM_PROMPT, user_prompt)
        parsed_dict = self._parse_json_response(raw_json_str)

        try:
            return AIErrorExplanationResponse(**parsed_dict)
        except ValidationError as e:
            logger.error(f"AIErrorExplanationResponse schema validation failed: {e}")
            raise AIResponseValidationError(f"Invalid error explanation schema: {e}")

    async def generate_recommendation(
        self,
        target_companies: List[str],
        skill_level: str,
        weak_topics: List[str],
        available_problems: List[Dict[str, Any]],
    ) -> AIRecommendationResponse:
        user_prompt = RECOMMENDATION_USER_TEMPLATE.format(
            target_companies=", ".join(target_companies),
            skill_level=skill_level,
            weak_topics=", ".join(weak_topics),
            available_problems_json=self._truncate_input(json.dumps(available_problems)),
        )

        raw_json_str = await self._generate_content_with_timeout(RECOMMENDATION_SYSTEM_PROMPT, user_prompt)
        parsed_dict = self._parse_json_response(raw_json_str)

        try:
            return AIRecommendationResponse(**parsed_dict)
        except ValidationError as e:
            logger.error(f"AIRecommendationResponse schema validation failed: {e}")
            raise AIResponseValidationError(f"Invalid recommendation schema: {e}")

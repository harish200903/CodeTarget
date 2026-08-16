import pytest
import uuid
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.config import settings
from app.services.ai.gemini import GeminiAIService
from app.services.ai.exceptions import (
    AIConfigurationError,
    AIProviderUnavailable,
    AIProviderTimeout,
    AIRateLimitExceeded,
    AIResponseValidationError,
)
from app.schemas.ai import (
    AIHintResponse,
    AICodeReviewResponse,
    AIErrorExplanationResponse,
    AIRecommendationResponse,
)
from app.services.ai.limiter import check_ai_rate_limit
from app.services.ai.cache import AICacheService, generate_ai_cache_key


@pytest.mark.asyncio
async def test_ai_disabled_configuration():
    """Verify that disabled AI raises AIConfigurationError cleanly."""
    with patch.object(settings, "AI_ENABLED", False):
        service = GeminiAIService(api_key="mock_key", model_name="gemini-2.5-flash")
        with pytest.raises(AIConfigurationError) as exc_info:
            await service.generate_hint("Two Sum", "EASY", "Desc", "Const", "code", "python", 1)
        assert "disabled" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_ai_missing_api_key():
    """Verify that missing GEMINI_API_KEY raises AIConfigurationError."""
    with patch.object(settings, "AI_ENABLED", True), patch.object(settings, "GEMINI_API_KEY", ""):
        service = GeminiAIService(api_key="", model_name="gemini-2.5-flash")
        with pytest.raises(AIConfigurationError) as exc_info:
            await service.generate_hint("Two Sum", "EASY", "Desc", "Const", "code", "python", 1)
        assert "api key" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_gemini_generate_hint_success():
    """Test successful AIHintResponse generation with mocked Gemini API."""
    mock_hint_payload = {
        "hint_text": "Consider using a hash map to store visited elements.",
        "hint_level": 1,
        "should_reveal_solution": False,
        "focus_concept": "Hash Map O(1) Lookups"
    }

    service = GeminiAIService(api_key="mock_test_key", model_name="gemini-2.5-flash")

    with patch.object(settings, "AI_ENABLED", True), patch.object(
        service, "_generate_content_with_timeout", new=AsyncMock(return_value=json.dumps(mock_hint_payload))
    ):
        res = await service.generate_hint(
            problem_title="Two Sum",
            difficulty="EASY",
            description="Find two numbers summing to target",
            constraints="2 <= N <= 10^4",
            user_code="def two_sum(): pass",
            language="python",
            hint_level=1
        )
        assert isinstance(res, AIHintResponse)
        assert res.hint_text == "Consider using a hash map to store visited elements."
        assert res.hint_level == 1
        assert res.focus_concept == "Hash Map O(1) Lookups"


@pytest.mark.asyncio
async def test_gemini_review_code_success():
    """Test successful AICodeReviewResponse generation with mocked Gemini API."""
    mock_review_payload = {
        "summary": "Efficient hash map solution.",
        "correctness_assessment": "Solution is logically correct.",
        "time_complexity": "O(N)",
        "space_complexity": "O(N)",
        "strengths": ["Single pass traversal", "O(1) lookups"],
        "improvements": ["Variable naming clarity"],
        "bugs": [],
        "suggestions": ["Add type hints"]
    }

    service = GeminiAIService(api_key="mock_test_key", model_name="gemini-2.5-flash")

    with patch.object(settings, "AI_ENABLED", True), patch.object(
        service, "_generate_content_with_timeout", new=AsyncMock(return_value=json.dumps(mock_review_payload))
    ):
        res = await service.review_code(
            problem_title="Two Sum",
            difficulty="EASY",
            description="Find two numbers summing to target",
            user_code="def two_sum(nums, target): return [0, 1]",
            language="python"
        )
        assert isinstance(res, AICodeReviewResponse)
        assert res.time_complexity == "O(N)"
        assert res.space_complexity == "O(N)"
        assert len(res.strengths) == 2


@pytest.mark.asyncio
async def test_gemini_explain_error_success():
    """Test successful AIErrorExplanationResponse generation."""
    mock_error_payload = {
        "error_type": "IndexError",
        "explanation": "List index out of range at line 4.",
        "suggested_direction": "Check boundary conditions for len(nums).",
        "key_line_number": 4
    }

    service = GeminiAIService(api_key="mock_test_key", model_name="gemini-2.5-flash")

    with patch.object(settings, "AI_ENABLED", True), patch.object(
        service, "_generate_content_with_timeout", new=AsyncMock(return_value=json.dumps(mock_error_payload))
    ):
        res = await service.explain_error(
            user_code="def two_sum(nums):\n return nums[100]",
            language="python",
            error_output="IndexError: list index out of range"
        )
        assert isinstance(res, AIErrorExplanationResponse)
        assert res.error_type == "IndexError"
        assert res.key_line_number == 4


@pytest.mark.asyncio
async def test_gemini_timeout_handling():
    """Test AIProviderTimeout handling."""
    service = GeminiAIService(api_key="mock_test_key", model_name="gemini-2.5-flash")

    with patch.object(settings, "AI_ENABLED", True), patch.object(
        service, "_generate_content_with_timeout", new=AsyncMock(side_effect=AIProviderTimeout("Timed out"))
    ):
        with pytest.raises(AIProviderTimeout):
            await service.explain_error("code", "python", "error")


@pytest.mark.asyncio
async def test_gemini_invalid_schema_parsing():
    """Test AIResponseValidationError when model output fails Pydantic schema validation."""
    service = GeminiAIService(api_key="mock_test_key", model_name="gemini-2.5-flash")
    invalid_json = '{"invalid_field": "test"}'

    with patch.object(settings, "AI_ENABLED", True), patch.object(
        service, "_generate_content_with_timeout", new=AsyncMock(return_value=invalid_json)
    ):
        with pytest.raises(AIResponseValidationError):
            await service.explain_error("code", "python", "error")


@pytest.mark.asyncio
async def test_ai_rate_limiter():
    """Test Redis sliding window AI rate limiter behavior."""
    mock_redis = MagicMock()
    mock_pipeline = MagicMock()
    mock_redis.pipeline.return_value = mock_pipeline

    # Case 1: Under limit
    mock_pipeline.execute = AsyncMock(return_value=[0, 5, 1, True])
    await check_ai_rate_limit(uuid.uuid4(), mock_redis)  # Should pass without error

    # Case 2: Rate limit exceeded (10+)
    mock_pipeline.execute = AsyncMock(return_value=[0, 10, 1, True])
    with pytest.raises(AIRateLimitExceeded):
        await check_ai_rate_limit(uuid.uuid4(), mock_redis)


@pytest.mark.asyncio
async def test_ai_caching_strategy():
    """Test AI Cache key generation and hit/miss behavior."""
    mock_payload = {"hint_level": 1, "problem_title": "Two Sum"}
    cache_key = generate_ai_cache_key("hint", mock_payload)
    assert cache_key.startswith("ai_cache:hint:")

    mock_redis = AsyncMock()
    cache_service = AICacheService(redis_client=mock_redis)

    # Set cache
    await cache_service.set(cache_key, {"hint_text": "Cached hint"})
    mock_redis.set.assert_called_once()

    # Get cache hit
    mock_redis.get.return_value = json.dumps({"hint_text": "Cached hint"})
    res = await cache_service.get(cache_key)
    assert res == {"hint_text": "Cached hint"}

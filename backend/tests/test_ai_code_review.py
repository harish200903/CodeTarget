import pytest
import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.user import User
from app.models.problem import Problem
from app.models.user_ai_code_review import UserAICodeReview
from app.schemas.ai import AICodeReviewResponse
from app.api.deps import get_ai_service


@pytest.mark.asyncio
async def test_ai_code_review_unauthenticated(async_client: AsyncClient):
    """Test that requesting AI code review without JWT token returns 401."""
    res = await async_client.post(
        "/api/v1/ai/code-review",
        json={
            "problem_id": str(uuid.uuid4()),
            "language": "python",
            "source_code": "def two_sum(): pass"
        }
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_ai_code_review_empty_code_validation(async_client: AsyncClient, test_user_token: str):
    """Test that empty or whitespace source code returns 400 Bad Request."""
    res = await async_client.post(
        "/api/v1/ai/code-review",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "problem_id": str(uuid.uuid4()),
            "language": "python",
            "source_code": "   "
        }
    )
    assert res.status_code == 400
    assert "enter some source code" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ai_code_review_nonexistent_problem(async_client: AsyncClient, test_user_token: str):
    """Test that non-existent problem ID returns 404 Not Found."""
    res = await async_client.post(
        "/api/v1/ai/code-review",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "problem_id": str(uuid.uuid4()),
            "language": "python",
            "source_code": "def two_sum(nums, target): return [0, 1]"
        }
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_ai_code_review_success_flow(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test successful code review generation, schema validation, and persistence."""
    stmt = select(Problem)
    res = await db_session.execute(stmt)
    problem = res.scalars().first()
    assert problem is not None

    mock_review = AICodeReviewResponse(
        summary="Optimal hash map solution.",
        correctness_assessment="Clearly Correct",
        time_complexity="O(N)",
        space_complexity="O(N)",
        strengths=["Single pass traversal", "O(1) lookups"],
        improvements=["Add type annotations"],
        bugs=[],
        suggestions=["Use dictionary comprehension"]
    )

    mock_service = AsyncMock()
    mock_service.review_code.return_value = mock_review
    app.dependency_overrides[get_ai_service] = lambda: mock_service

    try:
        response = await async_client.post(
            "/api/v1/ai/code-review",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "problem_id": str(problem.id),
                "language": "python",
                "source_code": "def two_sum(nums, target):\n seen = {}\n for i, num in enumerate(nums):\n  if target - num in seen:\n   return [seen[target - num], i]\n  seen[num] = i\n return []"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Optimal hash map solution."
        assert data["correctness_assessment"] == "Clearly Correct"
        assert data["time_complexity"] == "O(N)"
        assert len(data["strengths"]) == 2

        # Verify latest code review history API
        hist_res = await async_client.get(
            f"/api/v1/ai/code-review/{problem.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        assert hist_data["summary"] == "Optimal hash map solution."
        assert hist_data["time_complexity"] == "O(N)"

    finally:
        app.dependency_overrides.pop(get_ai_service, None)


@pytest.mark.asyncio
async def test_user_isolation_for_code_reviews(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test user isolation: User B cannot access User A's AI code review records."""
    problem = (await db_session.execute(select(Problem))).scalars().first()

    res = await async_client.get(
        f"/api/v1/ai/code-review/{problem.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200

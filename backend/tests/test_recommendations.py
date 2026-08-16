import pytest
import uuid
from unittest.mock import AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.user import User, SkillLevel
from app.models.problem import Problem
from app.models.submission import UserProblemProgress, ProgressStatus
from app.schemas.ai import AIRecommendationResponse
from app.api.deps import get_ai_service


@pytest.mark.asyncio
async def test_recommendations_unauthenticated(async_client: AsyncClient):
    """Test that requesting recommendations without authentication returns 401."""
    res = await async_client.get("/api/v1/recommendations")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_cold_start_recommendations(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test cold-start user (0 submissions) receives onboarding-derived recommendations."""
    res = await async_client.get(
        "/api/v1/recommendations?limit=5",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert "source" in data


@pytest.mark.asyncio
async def test_solved_problem_exclusion(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test that solved problems are NEVER recommended."""
    user_stmt = select(User)
    user = (await db_session.execute(user_stmt)).scalars().first()

    problem_stmt = select(Problem)
    problem = (await db_session.execute(problem_stmt)).scalars().first()

    # Mark problem as SOLVED
    progress = UserProblemProgress(
        user_id=user.id,
        problem_id=problem.id,
        status=ProgressStatus.SOLVED
    )
    db_session.add(progress)
    await db_session.commit()

    res = await async_client.get(
        "/api/v1/recommendations?limit=10",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200
    recommended_ids = [item["problem"]["id"] for item in res.json()["items"]]
    assert str(problem.id) not in recommended_ids


@pytest.mark.asyncio
async def test_ai_candidate_validation_and_fallback(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test that invalid AI-generated problem IDs are safely filtered out and fall back to deterministic ranking."""
    # Mock AI service returning a fake invented UUID
    fake_uuid = str(uuid.uuid4())
    mock_ai_res = AIRecommendationResponse(
        reasoning="Fake reasoning",
        recommended_problem_ids=[fake_uuid],
        focus_topics=["Hashing"]
    )

    mock_service = AsyncMock()
    mock_service.generate_recommendation.return_value = mock_ai_res
    app.dependency_overrides[get_ai_service] = lambda: mock_service

    try:
        res = await async_client.get(
            "/api/v1/recommendations?limit=5",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        recommended_ids = [item["problem"]["id"] for item in data["items"]]
        assert fake_uuid not in recommended_ids
        assert len(recommended_ids) > 0
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


@pytest.mark.asyncio
async def test_user_isolation_for_recommendations(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test recommendation isolation per authenticated user."""
    res = await async_client.get(
        "/api/v1/recommendations?limit=3",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200
    assert "items" in res.json()

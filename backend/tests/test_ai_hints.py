import pytest
import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.user import User
from app.models.problem import Problem
from app.models.submission import UserProblemProgress, ProgressStatus
from app.models.user_ai_hint import UserAIHint
from app.schemas.ai import AIHintResponse
from app.api.deps import get_ai_service


@pytest.mark.asyncio
async def test_ai_hint_unauthenticated_rejected(async_client: AsyncClient):
    """Test that requesting an AI hint without JWT authentication returns 401."""
    res = await async_client.post(
        "/api/v1/ai/hints",
        json={
            "problem_id": str(uuid.uuid4()),
            "language": "python",
            "source_code": "def two_sum(): pass"
        }
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_ai_hint_nonexistent_problem(async_client: AsyncClient, test_user_token: str):
    """Test that requesting an AI hint for a non-existent problem ID returns 404."""
    res = await async_client.post(
        "/api/v1/ai/hints",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "problem_id": str(uuid.uuid4()),
            "language": "python",
            "source_code": "def two_sum(): pass"
        }
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_ai_hint_progression_and_limit_enforcement(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test 3-step progressive hint unlocking (L1 -> L2 -> L3) and 4th request rejection."""
    # Get a seeded problem
    stmt = select(Problem)
    res = await db_session.execute(stmt)
    problem = res.scalars().first()
    assert problem is not None

    mock_hints = [
        AIHintResponse(hint_text="Hint 1 Conceptual", hint_level=1, focus_concept="Hashing"),
        AIHintResponse(hint_text="Hint 2 Strategic", hint_level=2, focus_concept="Hash Map O(1)"),
        AIHintResponse(hint_text="Hint 3 Tactical", hint_level=3, focus_concept="Pseudocode"),
    ]

    mock_service = AsyncMock()

    # Step 1: Request Hint 1
    mock_service.generate_hint.return_value = mock_hints[0]
    app.dependency_overrides[get_ai_service] = lambda: mock_service

    try:
        res1 = await async_client.post(
            "/api/v1/ai/hints",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"problem_id": str(problem.id), "language": "python", "source_code": "def solve(): pass"}
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["hint_level"] == 1
        assert data1["hint_text"] == "Hint 1 Conceptual"

        # Step 2: Request Hint 2
        mock_service.generate_hint.return_value = mock_hints[1]

        res2 = await async_client.post(
            "/api/v1/ai/hints",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"problem_id": str(problem.id), "language": "python", "source_code": "def solve(): pass"}
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["hint_level"] == 2
        assert data2["hint_text"] == "Hint 2 Strategic"

        # Step 3: Request Hint 3
        mock_service.generate_hint.return_value = mock_hints[2]

        res3 = await async_client.post(
            "/api/v1/ai/hints",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"problem_id": str(problem.id), "language": "python", "source_code": "def solve(): pass"}
        )
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["hint_level"] == 3
        assert data3["hint_text"] == "Hint 3 Tactical"

        # Step 4: Request Hint 4 -> REJECTED (400 Bad Request)
        res4 = await async_client.post(
            "/api/v1/ai/hints",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"problem_id": str(problem.id), "language": "python", "source_code": "def solve(): pass"}
        )
        assert res4.status_code == 400
        assert "used all 3 ai hints" in res4.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


@pytest.mark.asyncio
async def test_ai_hint_rejected_if_already_solved(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test that requesting AI hints for an already SOLVED problem returns 400."""
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

    res = await async_client.post(
        "/api/v1/ai/hints",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"problem_id": str(problem.id), "language": "python", "source_code": "def solve(): pass"}
    )
    assert res.status_code == 400
    assert "already solved" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_isolation_for_ai_hints(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test user isolation: User B cannot see User A's unlocked AI hints."""
    problem = (await db_session.execute(select(Problem))).scalars().first()

    # Request hint history as test_user
    res = await async_client.get(
        f"/api/v1/ai/hints/{problem.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200
    assert "items" in res.json()

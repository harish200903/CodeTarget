import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User, UserTargetCompany
from app.models.company import Company
from app.models.problem import Problem
from app.models.submission import UserProblemProgress, ProgressStatus


@pytest.mark.asyncio
async def test_company_prep_unauthenticated(async_client: AsyncClient):
    """Test that requesting company preparation metrics without auth returns 401."""
    res = await async_client.get(f"/api/v1/companies/{uuid.uuid4()}/preparation")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_unselected_company_access_forbidden(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test that requesting preparation for an unselected target company returns 403 Forbidden."""
    unselected_id = str(uuid.uuid4())
    res = await async_client.get(
        f"/api/v1/companies/{unselected_id}/preparation",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 403
    assert "not in your selected target companies" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_company_prep_cold_start_state(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test cold-start state (< 2 attempted problems) returns INSUFFICIENT_DATA and None score."""
    user = (await db_session.execute(select(User))).scalars().first()
    assert user is not None

    company = (await db_session.execute(select(Company))).scalars().first()
    assert company is not None

    tc = UserTargetCompany(user_id=user.id, company_id=company.id, priority=1)
    db_session.add(tc)
    await db_session.commit()

    res = await async_client.get(
        f"/api/v1/companies/{company.id}/preparation",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INSUFFICIENT_DATA"
    assert data["preparation_score"] is None
    assert "establish your CodeTarget preparation baseline" in data["confidence_message"]


@pytest.mark.asyncio
async def test_company_prep_deterministic_scoring(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test deterministic preparation score calculation and topic/difficulty analytics."""
    user = (await db_session.execute(select(User))).scalars().first()
    company = (await db_session.execute(select(Company))).scalars().first()
    assert company is not None

    tc = UserTargetCompany(user_id=user.id, company_id=company.id, priority=1)
    db_session.add(tc)

    # Fetch 2 problems for this target company
    probs = (await db_session.execute(select(Problem))).scalars().all()[:2]
    assert len(probs) >= 2

    # Mark problems as solved
    for p in probs:
        progress = UserProblemProgress(
            user_id=user.id,
            problem_id=p.id,
            status=ProgressStatus.SOLVED,
            attempts_count=1
        )
        db_session.add(progress)
    await db_session.commit()

    res = await async_client.get(
        f"/api/v1/companies/{company.id}/preparation",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200
    data = res.json()

    # Score should now be calculated
    assert data["preparation_score"] is not None
    assert 0 <= data["preparation_score"] <= 100
    assert data["status"] in ("STARTING", "DEVELOPING", "WELL_PREPARED")
    assert "coverage" in data
    assert "topic_breakdown" in data
    assert "difficulty_breakdown" in data
    assert len(data["strengths"]) > 0
    assert len(data["recommended_next_steps"]) > 0

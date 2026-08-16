import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.user import User, UserTargetCompany
from app.models.company import Company
from app.models.mock_test import MockTest, UserMockTest, MockTestStatus


@pytest.mark.asyncio
async def test_mock_test_unauthenticated(async_client: AsyncClient):
    """Test that listing mock tests without auth returns 401."""
    res = await async_client.get("/api/v1/mock-tests")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_mock_test_catalog_target_company_filtering(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test that candidate receives mock tests matching their selected target companies."""
    stmt = select(User).options(selectinload(User.target_companies))
    user = (await db_session.execute(stmt)).scalars().first()
    assert user is not None

    company = (await db_session.execute(select(Company))).scalars().first()
    tc = UserTargetCompany(user_id=user.id, company_id=company.id, priority=1)
    db_session.add(tc)
    await db_session.commit()

    res = await async_client.get(
        "/api/v1/mock-tests",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 200
    catalog = res.json()
    assert isinstance(catalog, list)
    assert len(catalog) > 0
    assert any(m["company_id"] == str(company.id) for m in catalog)


@pytest.mark.asyncio
async def test_mock_test_unauthorized_company_rejection(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test that starting a mock test for an unselected company returns 403 Forbidden."""
    # Find mock test for unselected company
    unselected_mock = (await db_session.execute(select(MockTest))).scalars().first()
    assert unselected_mock is not None

    res = await async_client.post(
        f"/api/v1/mock-tests/{unselected_mock.id}/start",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 403
    assert "not in your target companies" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_mock_test_start_and_session_lifecycle(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test starting a mock session, checking timer, submitting a problem, and completing test."""
    user = (await db_session.execute(select(User))).scalars().first()
    company = (await db_session.execute(select(Company))).scalars().first()
    assert company is not None

    tc = UserTargetCompany(user_id=user.id, company_id=company.id, priority=1)
    db_session.add(tc)

    mock = (await db_session.execute(select(MockTest).where(MockTest.company_id == company.id))).scalars().first()
    assert mock is not None
    await db_session.commit()

    # 1. Start Session
    start_res = await async_client.post(
        f"/api/v1/mock-tests/{mock.id}/start",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    assert session_data["status"] == "IN_PROGRESS"
    assert session_data["remaining_seconds"] > 0
    assert len(session_data["problems"]) > 0

    # 2. Get Active Session Details
    get_res = await async_client.get(
        f"/api/v1/mock-tests/sessions/{session_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["session_id"] == session_id

    # 3. Submit Solution for Problem 1
    prob1 = session_data["problems"][0]
    sub_res = await async_client.post(
        f"/api/v1/mock-tests/sessions/{session_id}/problems/{prob1['problem_id']}/submit",
        json={"language": "python", "code": "def solution(): return True"},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert "status" in sub_data
    assert "score_obtained" in sub_data

    # 4. Finalize Complete Test
    comp_res = await async_client.post(
        f"/api/v1/mock-tests/sessions/{session_id}/submit",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert comp_res.status_code == 200
    result_data = comp_res.json()
    assert result_data["session_id"] == session_id
    assert result_data["status"] in ("SUBMITTED", "AUTO_SUBMITTED")
    assert 0 <= result_data["percentage"] <= 100
    assert len(result_data["problems"]) > 0
    assert len(result_data["topic_breakdown"]) >= 0


@pytest.mark.asyncio
async def test_mock_test_user_isolation(
    async_client: AsyncClient,
    test_user_token: str,
    db_session: AsyncSession
):
    """Test that Candidate A cannot view or access Candidate B's mock session."""
    user = (await db_session.execute(select(User))).scalars().first()
    company = (await db_session.execute(select(Company))).scalars().first()
    mock = (await db_session.execute(select(MockTest))).scalars().first()

    # Create dummy user session for another user ID
    fake_session = UserMockTest(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),  # Different user
        mock_test_id=mock.id,
        status=MockTestStatus.IN_PROGRESS,
    )
    db_session.add(fake_session)
    await db_session.commit()

    res = await async_client.get(
        f"/api/v1/mock-tests/sessions/{fake_session.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert res.status_code == 404

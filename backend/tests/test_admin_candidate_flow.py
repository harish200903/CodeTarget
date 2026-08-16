import pytest
import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from app.models.user import User, UserRole, SkillLevel
from app.core.security import create_access_token
from app.services.execution import BatchExecutionResult, SingleTestCaseResult
from app.models.submission import SubmissionStatus


@pytest.fixture
async def admin_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="admin_flow@codetarget.com",
        password_hash="pw",
        role=UserRole.ADMIN,
        skill_level=SkillLevel.ADVANCED,
        onboarding_completed=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
def admin_headers(admin_user):
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def candidate_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="candidate_flow@codetarget.com",
        password_hash="pw",
        role=UserRole.USER,
        skill_level=SkillLevel.BEGINNER,
        onboarding_completed=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
def candidate_headers(candidate_user):
    token = create_access_token(data={"sub": str(candidate_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_created_content_candidate_flow(async_client: AsyncClient, admin_headers, candidate_headers):
    # 1. Admin creates company
    c_res = await async_client.post(
        "/api/v1/admin/companies",
        json={"name": "Flow Corp", "slug": "flow-corp", "tier": "TIER_1", "description": "Flow testing"},
        headers=admin_headers,
    )
    assert c_res.status_code == 201
    company_id = c_res.json()["id"]

    # 2. Admin creates topic
    t_res = await async_client.post(
        "/api/v1/admin/topics",
        json={"name": "Flow Graphs", "slug": "flow-graphs", "description": "Graph algorithms"},
        headers=admin_headers,
    )
    assert t_res.status_code == 201
    topic_id = t_res.json()["id"]

    # 3. Admin creates active problem
    p_res = await async_client.post(
        "/api/v1/admin/problems",
        json={
            "title": "Flow BFS",
            "slug": "flow-bfs",
            "difficulty": "MEDIUM",
            "category": "Graphs",
            "description_markdown": "Perform BFS traversal.",
            "constraints_text": "1 <= N <= 100",
            "starter_code": {"python": "def bfs(): pass"},
            "company_ids": [company_id],
            "topic_ids": [topic_id],
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert p_res.status_code == 201
    prob_id = p_res.json()["id"]

    # 4. Admin adds test case and hint
    tc_res = await async_client.post(
        f"/api/v1/admin/problems/{prob_id}/test-cases",
        json={"input_data": "0", "expected_output": "0", "is_sample": True},
        headers=admin_headers,
    )
    assert tc_res.status_code == 201

    h_res = await async_client.post(
        f"/api/v1/admin/problems/{prob_id}/hints",
        json={"step_number": 1, "title": "Use Queue", "content_markdown": "Use a FIFO queue for BFS."},
        headers=admin_headers,
    )
    assert h_res.status_code == 201

    # 5. Candidate queries problem catalog
    cat_res = await async_client.get("/api/v1/problems", headers=candidate_headers)
    assert cat_res.status_code == 200
    assert any(p["id"] == prob_id for p in cat_res.json()["items"])

    # 6. Candidate views problem detail
    det_res = await async_client.get("/api/v1/problems/flow-bfs", headers=candidate_headers)
    assert det_res.status_code == 200
    assert det_res.json()["title"] == "Flow BFS"

    # 7. Candidate solves problem
    mock_batch = BatchExecutionResult(
        overall_status=SubmissionStatus.ACCEPTED,
        passed_test_cases=1,
        total_test_cases=1,
        execution_time_ms=15,
        memory_kb=1024,
        test_case_results=[
            SingleTestCaseResult(passed=True, input_data="0", expected_output="0", actual_output="0", status=SubmissionStatus.ACCEPTED)
        ],
    )

    with patch("app.services.execution.Judge0ExecutionService.execute_submission", new=AsyncMock(return_value=mock_batch)):
        sub_res = await async_client.post(
            "/api/v1/submissions/submit",
            json={"problem_id": prob_id, "language": "python", "code": "def bfs(): return 0"},
            headers=candidate_headers,
        )
        assert sub_res.status_code == 200
        assert sub_res.json()["status"] == "ACCEPTED"

    # 8. Candidate receives Gamification XP award (+20 XP for Medium solve)
    gami_res = await async_client.get("/api/v1/gamification/me", headers=candidate_headers)
    assert gami_res.status_code == 200
    assert gami_res.json()["total_xp"] >= 20

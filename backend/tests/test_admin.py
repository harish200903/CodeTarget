import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient
from app.models.user import User, UserRole, SkillLevel
from app.models.company import Company
from app.models.problem import Problem, Topic, DifficultyLevel, TestCase as ProblemTestCase, Hint
from app.models.submission import Submission
from app.models.audit import AuditLog
from app.core.security import create_access_token


@pytest.fixture
async def admin_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="admin@codetarget.com",
        password_hash="hashed_pw",
        role=UserRole.ADMIN,
        skill_level=SkillLevel.ADVANCED,
        onboarding_completed=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user):
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def candidate_headers(test_user_token):
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.mark.asyncio
async def test_unauthenticated_admin_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/admin/dashboard")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_candidate_forbidden_admin_endpoint(async_client: AsyncClient, candidate_headers):
    res = await async_client.get("/api/v1/admin/dashboard", headers=candidate_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Admin privileges required for this action"


@pytest.mark.asyncio
async def test_admin_dashboard_summary(async_client: AsyncClient, admin_headers):
    res = await async_client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "companies_count" in data
    assert "topics_count" in data
    assert "problems_count" in data
    assert "active_problems_count" in data
    assert "mock_tests_count" in data
    assert "total_test_cases" in data
    assert "total_hints" in data


@pytest.mark.asyncio
async def test_admin_company_lifecycle(async_client: AsyncClient, admin_headers):
    # 1. Create company
    create_body = {
        "name": "Admin Test Corp",
        "slug": "admin-test-corp",
        "tier": "FAANG",
        "description": "High tier company",
    }
    res = await async_client.post("/api/v1/admin/companies", json=create_body, headers=admin_headers)
    assert res.status_code == 201
    c_id = res.json()["id"]

    # 2. List companies
    res = await async_client.get("/api/v1/admin/companies", headers=admin_headers)
    assert res.status_code == 200
    comp_list = res.json()
    assert any(c["slug"] == "admin-test-corp" for c in comp_list)

    # 3. Update company
    res = await async_client.patch(f"/api/v1/admin/companies/{c_id}", json={"name": "Updated Corp"}, headers=admin_headers)
    assert res.status_code == 200

    # 4. Check audit log
    res = await async_client.get("/api/v1/admin/audit-logs?resource_type=company", headers=admin_headers)
    assert res.status_code == 200
    logs = res.json()["items"]
    assert any(log["action"] == "CREATE_COMPANY" for log in logs)


@pytest.mark.asyncio
async def test_admin_topic_lifecycle(async_client: AsyncClient, admin_headers):
    # 1. Create topic
    res = await async_client.post(
        "/api/v1/admin/topics",
        json={"name": "Segment Trees", "slug": "segment-trees", "description": "Advanced tree structure"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    t_id = res.json()["id"]

    # 2. List topics
    res = await async_client.get("/api/v1/admin/topics", headers=admin_headers)
    assert res.status_code == 200
    assert any(t["slug"] == "segment-trees" for t in res.json())

    # 3. Edit topic
    res = await async_client.patch(f"/api/v1/admin/topics/{t_id}", json={"name": "Segment Tree Algo"}, headers=admin_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_admin_problem_lifecycle_and_security(async_client: AsyncClient, admin_headers, candidate_headers):
    # 1. Create company and topic
    c_res = await async_client.post(
        "/api/v1/admin/companies",
        json={"name": "Meta", "slug": "meta", "tier": "FAANG"},
        headers=admin_headers,
    )
    c_id = c_res.json()["id"]

    t_res = await async_client.post(
        "/api/v1/admin/topics",
        json={"name": "Tries", "slug": "tries"},
        headers=admin_headers,
    )
    t_id = t_res.json()["id"]

    # 2. Create problem
    prob_body = {
        "title": "Implement Trie",
        "slug": "implement-trie-admin",
        "difficulty": "MEDIUM",
        "category": "Trees & Tries",
        "description_markdown": "A trie or prefix tree is a tree data structure...",
        "starter_code": {"python": "class Trie:\n    pass"},
        "company_ids": [c_id],
        "topic_ids": [t_id],
    }
    p_res = await async_client.post("/api/v1/admin/problems", json=prob_body, headers=admin_headers)
    assert p_res.status_code == 201
    p_id = p_res.json()["id"]

    # 3. Add test cases (1 public, 1 hidden)
    tc1 = await async_client.post(
        f"/api/v1/admin/problems/{p_id}/test-cases",
        json={"input_data": "insert apple", "expected_output": "null", "is_sample": True},
        headers=admin_headers,
    )
    assert tc1.status_code == 201

    tc2 = await async_client.post(
        f"/api/v1/admin/problems/{p_id}/test-cases",
        json={"input_data": "search app", "expected_output": "false", "is_sample": False},
        headers=admin_headers,
    )
    assert tc2.status_code == 201

    # 4. Verify candidate endpoint DOES NOT expose hidden test cases
    cand_res = await async_client.get("/api/v1/problems/implement-trie-admin", headers=candidate_headers)
    assert cand_res.status_code == 200
    cand_data = cand_res.json()
    sample_cases = cand_data["sample_test_cases"]
    assert len(sample_cases) == 1
    assert sample_cases[0]["is_sample"] is True
    assert "search app" not in [tc["input_data"] for tc in sample_cases]

    # 5. Verify admin detail endpoint includes test cases
    adm_res = await async_client.get(f"/api/v1/admin/problems/{p_id}", headers=admin_headers)
    assert adm_res.status_code == 200
    assert len(adm_res.json()["test_cases"]) == 2


@pytest.mark.asyncio
async def test_admin_soft_deactivation_preserves_submissions(async_client: AsyncClient, admin_headers, db_session):
    # Create user
    user = User(
        id=uuid.uuid4(),
        email="candidate_test@codetarget.com",
        password_hash="pw",
        role=UserRole.USER,
        skill_level=SkillLevel.BEGINNER,
        onboarding_completed=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Create problem
    prob = Problem(
        id=uuid.uuid4(),
        title="Problem to Deactivate",
        slug="prob-deactivate",
        difficulty=DifficultyLevel.EASY,
        category="Arrays",
        description_markdown="Test description",
        starter_code={"python": "pass"},
    )
    db_session.add(prob)
    await db_session.flush()

    # Create submission for user
    sub = Submission(
        id=uuid.uuid4(),
        user_id=user.id,
        problem_id=prob.id,
        language="python",
        code="pass",
        status="ACCEPTED",
        passed_test_cases=1,
        total_test_cases=1,
    )
    db_session.add(sub)
    await db_session.commit()

    # Admin soft-deactivates problem
    res = await async_client.delete(f"/api/v1/admin/problems/{prob.id}", headers=admin_headers)
    assert res.status_code == 200

    # Verify problem category is now INACTIVE
    await db_session.refresh(prob)
    assert prob.category == "INACTIVE"

    # Verify submission remains intact in DB
    sub_check = (await db_session.get(Submission, sub.id))
    assert sub_check is not None
    assert sub_check.status == "ACCEPTED"


@pytest.mark.asyncio
async def test_admin_audit_logs_security(async_client: AsyncClient, candidate_headers, admin_headers):
    # Candidate rejected
    res = await async_client.get("/api/v1/admin/audit-logs", headers=candidate_headers)
    assert res.status_code == 403

    # Admin allowed
    res = await async_client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert res.status_code == 200
    assert "items" in res.json()

import pytest
import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.future import select

from app.models.user import User, UserRole, SkillLevel
from app.models.company import Company
from app.models.problem import Problem, DifficultyLevel, TestCase as ProblemTestCase, Topic, ProblemTopic, ProblemCompany
from app.models.mock_test import MockTest, MockTestProblem
from app.services.execution import BatchExecutionResult, SingleTestCaseResult
from app.models.submission import SubmissionStatus
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_full_candidate_e2e_journey(async_client: AsyncClient, db_session):
    # 1. Register candidate user
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e_candidate@codetarget.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "full_name": "E2E Candidate",
        },
    )

    assert reg_res.status_code == 201

    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed company & topic
    comp = Company(id=uuid.uuid4(), name="E2E Corp", slug="e2e-corp", tier="Tier 1")
    topic = Topic(id=uuid.uuid4(), name="E2E Arrays", slug="e2e-arrays")
    db_session.add_all([comp, topic])
    await db_session.commit()

    # 3. Complete onboarding
    onboard_res = await async_client.patch(
        "/api/v1/users/onboarding",
        json={
            "target_company_ids": [str(comp.id)],
            "primary_company_id": str(comp.id),
            "preferred_language": "python",
            "skill_level": "INTERMEDIATE",
            "daily_goal_minutes": 30,
        },
        headers=headers,
    )
    assert onboard_res.status_code == 200
    assert onboard_res.json()["onboarding_completed"] is True

    # 4. Seed problem with test case
    prob = Problem(
        id=uuid.uuid4(),
        title="E2E Two Sum",
        slug="e2e-two-sum",
        difficulty=DifficultyLevel.EASY,
        category="Arrays",
        is_active=True,
        description_markdown="Find two indices.",
        starter_code={"python": "def two_sum(): pass"},
    )
    db_session.add(prob)
    await db_session.flush()

    db_session.add(ProblemTopic(id=uuid.uuid4(), problem_id=prob.id, topic_id=topic.id))
    db_session.add(ProblemCompany(id=uuid.uuid4(), problem_id=prob.id, company_id=comp.id))
    db_session.add(ProblemTestCase(id=uuid.uuid4(), problem_id=prob.id, input_data="[2,7]\n9", expected_output="[0,1]", is_sample=True))
    await db_session.commit()

    # 5. Fetch catalog
    cat_res = await async_client.get("/api/v1/problems", headers=headers)
    assert cat_res.status_code == 200
    assert any(p["id"] == str(prob.id) for p in cat_res.json()["items"])

    # 6. Submit solution
    mock_batch = BatchExecutionResult(
        overall_status=SubmissionStatus.ACCEPTED,
        passed_test_cases=1,
        total_test_cases=1,
        execution_time_ms=12,
        memory_kb=1024,
        test_case_results=[
            SingleTestCaseResult(passed=True, input_data="[2,7]\n9", expected_output="[0,1]", actual_output="[0,1]", status=SubmissionStatus.ACCEPTED)
        ],
    )

    with patch("app.services.execution.Judge0ExecutionService.execute_submission", new=AsyncMock(return_value=mock_batch)):
        sub_res = await async_client.post(
            "/api/v1/submissions/submit",
            json={"problem_id": str(prob.id), "language": "python", "code": "def two_sum(): return [0,1]"},
            headers=headers,
        )
        assert sub_res.status_code == 200
        assert sub_res.json()["status"] == "ACCEPTED"

    # 7. Verify Gamification update
    gami_res = await async_client.get("/api/v1/gamification/me", headers=headers)
    assert gami_res.status_code == 200
    gami_data = gami_res.json()
    assert gami_data["total_xp"] >= 10  # Solved Easy
    assert gami_data["current_streak"] == 1

    # 8. Verify Company Prep Intelligence update
    prep_res = await async_client.get(f"/api/v1/companies/{comp.id}/preparation", headers=headers)
    assert prep_res.status_code == 200
    prep_data = prep_res.json()
    assert prep_data["problems"]["solved"] >= 1

    # 9. Verify Opt-in Leaderboard
    opt_res = await async_client.patch("/api/v1/gamification/preferences", json={"leaderboard_opt_in": True, "display_name": "E2E Coder"}, headers=headers)
    assert opt_res.status_code == 200

    lead_res = await async_client.get("/api/v1/leaderboard", headers=headers)
    assert lead_res.status_code == 200
    assert any(u["display_name"] == "E2E Coder" for u in lead_res.json()["items"])

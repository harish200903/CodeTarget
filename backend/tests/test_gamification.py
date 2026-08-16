import pytest
import uuid
from datetime import datetime, timezone, date, timedelta
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.future import select

from app.models.user import User, UserRole, SkillLevel
from app.models.problem import Problem, DifficultyLevel, TestCase as ProblemTestCase
from app.models.submission import Submission, UserProblemProgress, SubmissionStatus, ProgressStatus
from app.models.mock_test import MockTest, UserMockTest, MockTestStatus
from app.models.company import Company
from app.models.gamification import UserGamification, XPTransaction, DailyActivity, Badge, UserBadge
from app.services.gamification import GamificationService, xp_required_for_level, calculate_level_from_xp
from app.services.execution import BatchExecutionResult, SingleTestCaseResult
from app.core.security import create_access_token


@pytest.fixture
async def test_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="gami_user@codetarget.com",
        password_hash="pw",
        role=UserRole.USER,
        skill_level=SkillLevel.BEGINNER,
        onboarding_completed=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def candidate_headers(test_user):
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_level_calculation_formula():
    assert xp_required_for_level(1) == 0
    assert xp_required_for_level(2) == 100
    assert xp_required_for_level(3) == 300
    assert xp_required_for_level(4) == 600

    lvl1, base1, next1, pct1 = calculate_level_from_xp(0)
    assert lvl1 == 1 and base1 == 0 and next1 == 100

    lvl2, base2, next2, pct2 = calculate_level_from_xp(150)
    assert lvl2 == 2 and base2 == 100 and next2 == 300 and pct2 == 25.0


@pytest.mark.asyncio
async def test_xp_award_and_idempotency(db_session, test_user):
    # 1. First award
    awarded = await GamificationService.award_xp(
        db=db_session,
        user_id=test_user.id,
        amount=50,
        reason="TEST_REASON",
        reference_type="test",
        reference_id="ref123",
    )
    assert awarded == 50

    profile = await GamificationService.get_or_create_profile(db_session, test_user.id)
    assert profile.total_xp == 50

    # 2. Duplicate award (same reason, reference_type, reference_id)
    dup_awarded = await GamificationService.award_xp(
        db=db_session,
        user_id=test_user.id,
        amount=50,
        reason="TEST_REASON",
        reference_type="test",
        reference_id="ref123",
    )
    assert dup_awarded == 0
    assert profile.total_xp == 50


@pytest.mark.asyncio
async def test_problem_solve_xp_integration(async_client: AsyncClient, candidate_headers, db_session, test_user):
    # Create Easy problem
    prob = Problem(
        id=uuid.uuid4(),
        title="Easy Gamification Test",
        slug="easy-gami-test",
        difficulty=DifficultyLevel.EASY,
        category="Arrays",
        description_markdown="Test",
        starter_code={"python": "pass"},
    )
    db_session.add(prob)
    tc = ProblemTestCase(id=uuid.uuid4(), problem_id=prob.id, input_data="1", expected_output="1", is_sample=True)
    db_session.add(tc)
    await db_session.commit()

    mock_batch_res = BatchExecutionResult(
        overall_status=SubmissionStatus.ACCEPTED,
        passed_test_cases=1,
        total_test_cases=1,
        execution_time_ms=10,
        memory_kb=512,
        test_case_results=[
            SingleTestCaseResult(
                passed=True,
                input_data="1",
                expected_output="1",
                actual_output="1",
                status=SubmissionStatus.ACCEPTED,
            )
        ],
    )

    sub_body = {"problem_id": str(prob.id), "language": "python", "code": "pass"}

    with patch("app.services.execution.Judge0ExecutionService.execute_submission", new=AsyncMock(return_value=mock_batch_res)):
        res = await async_client.post("/api/v1/submissions/submit", json=sub_body, headers=candidate_headers)
        assert res.status_code == 200

        # Check gamification profile
        gami_res = await async_client.get("/api/v1/gamification/me", headers=candidate_headers)
        assert gami_res.status_code == 200
        data = gami_res.json()
        assert data["total_xp"] >= 10  # Solved Easy (+10 XP)
        assert data["current_streak"] == 1

        # Second submission for SAME solved problem should NOT award duplicate solve XP
        res2 = await async_client.post("/api/v1/submissions/submit", json=sub_body, headers=candidate_headers)
        assert res2.status_code == 200

        gami_res2 = await async_client.get("/api/v1/gamification/me", headers=candidate_headers)
        data2 = gami_res2.json()
        assert data2["total_xp"] == data["total_xp"]  # XP un-incremented for duplicate solve


@pytest.mark.asyncio
async def test_streak_calculation_same_day_and_consecutive(db_session, test_user):
    profile = await GamificationService.get_or_create_profile(db_session, test_user.id)

    # 1. Day 1 activity
    s1 = await GamificationService.update_streak(db_session, test_user.id)
    assert s1 == 1
    assert profile.current_streak == 1

    # 2. Second activity on same day (must NOT increment streak twice)
    s2 = await GamificationService.update_streak(db_session, test_user.id)
    assert s2 == 1
    assert profile.current_streak == 1

    # 3. Simulate activity yesterday -> today
    profile.last_activity_date = date.today() - timedelta(days=1)
    await db_session.commit()

    s3 = await GamificationService.update_streak(db_session, test_user.id)
    assert s3 == 2
    assert profile.current_streak == 2
    assert profile.longest_streak == 2


@pytest.mark.asyncio
async def test_daily_goal_xp_award(db_session, test_user):
    act = await GamificationService.get_or_create_daily_activity(db_session, test_user.id)
    act.minutes_practiced = 35  # Exceeds goal_minutes (30)

    completed1 = await GamificationService.check_daily_goal_completion(db_session, test_user.id)
    assert completed1 is True

    profile = await GamificationService.get_or_create_profile(db_session, test_user.id)
    assert profile.total_xp >= 25  # Daily goal XP (+25)

    # Calling check again on same day should NOT award duplicate XP
    completed2 = await GamificationService.check_daily_goal_completion(db_session, test_user.id)
    assert completed2 is True


@pytest.mark.asyncio
async def test_badge_evaluation_and_idempotency(db_session, test_user):
    # Ensure badges exist in DB
    badge_stmt = select(Badge).where(Badge.slug == "first-steps")
    badge = (await db_session.execute(badge_stmt)).scalar_one_or_none()
    if not badge:
        badge = Badge(id=uuid.uuid4(), slug="first-steps", name="First Steps", description="Solve 1 problem", xp_reward=25)
        db_session.add(badge)
        await db_session.commit()

    # Add 1 solved problem progress
    prob_id = uuid.uuid4()
    prog = UserProblemProgress(id=uuid.uuid4(), user_id=test_user.id, problem_id=prob_id, status=ProgressStatus.SOLVED, attempts_count=1)
    db_session.add(prog)
    await db_session.commit()

    # Evaluate badges
    newly_awarded = await GamificationService.evaluate_badges(db_session, test_user.id)
    assert any(b.slug == "first-steps" for b in newly_awarded)

    # Second evaluation should return empty list (idempotent protection)
    dup_awarded = await GamificationService.evaluate_badges(db_session, test_user.id)
    assert len(dup_awarded) == 0


@pytest.mark.asyncio
async def test_leaderboard_privacy_and_opt_in(async_client: AsyncClient, candidate_headers, db_session, test_user):
    # 1. Opt out user (default)
    profile = await GamificationService.get_or_create_profile(db_session, test_user.id)
    profile.leaderboard_opt_in = False
    await db_session.commit()

    res = await async_client.get("/api/v1/leaderboard", headers=candidate_headers)
    assert res.status_code == 200
    data = res.json()
    # Opted out user is excluded from leaderboard items
    assert not any(item["user_id"] == str(test_user.id) for item in data["items"])

    # 2. Opt in user
    opt_res = await async_client.patch("/api/v1/gamification/preferences", json={"leaderboard_opt_in": True, "display_name": "Coder123"}, headers=candidate_headers)
    assert opt_res.status_code == 200

    res2 = await async_client.get("/api/v1/leaderboard", headers=candidate_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    # Opted in user appears in leaderboard
    user_item = next((item for item in data2["items"] if item["user_id"] == str(test_user.id)), None)
    assert user_item is not None
    assert user_item["display_name"] == "Coder123"
    # Ensure NO passwords or emails exposed in payload
    assert "email" not in user_item
    assert "password" not in user_item

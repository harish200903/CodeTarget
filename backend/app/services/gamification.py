import math
import uuid
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_

from app.models.user import User
from app.models.problem import Problem, DifficultyLevel
from app.models.submission import Submission, UserProblemProgress
from app.models.mock_test import UserMockTest, MockTest
from app.models.gamification import (
    UserGamification,
    XPTransaction,
    DailyActivity,
    Badge,
    UserBadge,
)

logger = logging.getLogger(__name__)


def xp_required_for_level(level: int) -> int:
    """Calculates total XP required to reach level N.
    Formula: 100 * N * (N - 1) / 2
    Level 1: 0
    Level 2: 100
    Level 3: 300
    Level 4: 600
    Level 5: 1000...
    """
    if level <= 1:
        return 0
    return 100 * level * (level - 1) // 2


def calculate_level_from_xp(total_xp: int) -> Tuple[int, int, int, float]:
    """Given total XP, calculates:
    (current_level, xp_for_current_level, xp_for_next_level, progress_pct)
    """
    if total_xp <= 0:
        return 1, 0, 100, 0.0

    level = 1
    while xp_required_for_level(level + 1) <= total_xp:
        level += 1

    current_lvl_base = xp_required_for_level(level)
    next_lvl_base = xp_required_for_level(level + 1)

    xp_in_level = total_xp - current_lvl_base
    range_for_level = next_lvl_base - current_lvl_base
    progress_pct = round((xp_in_level / range_for_level) * 100, 1) if range_for_level > 0 else 100.0

    return level, current_lvl_base, next_lvl_base, progress_pct


class GamificationService:
    @staticmethod
    async def get_or_create_profile(db: AsyncSession, user_id: uuid.UUID) -> UserGamification:
        """Retrieves or initializes the user's gamification profile."""
        stmt = select(UserGamification).where(UserGamification.user_id == user_id)
        profile = (await db.execute(stmt)).scalar_one_or_none()

        if not profile:
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
            display_name = user.full_name or user.email.split("@")[0] if user else f"Candidate_{str(user_id)[:6]}"
            profile = UserGamification(
                id=uuid.uuid4(),
                user_id=user_id,
                total_xp=0,
                current_level=1,
                current_streak=0,
                longest_streak=0,
                last_activity_date=None,
                leaderboard_opt_in=False,
                display_name=display_name,
            )
            db.add(profile)
            await db.flush()

        return profile

    @staticmethod
    async def get_or_create_daily_activity(
        db: AsyncSession, user_id: uuid.UUID, target_date: Optional[date] = None
    ) -> DailyActivity:
        """Retrieves or creates a DailyActivity record for user on target_date."""
        act_date = target_date or date.today()
        stmt = select(DailyActivity).where(
            and_(DailyActivity.user_id == user_id, DailyActivity.activity_date == act_date)
        )
        act = (await db.execute(stmt)).scalar_one_or_none()

        if not act:
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
            goal_mins = user.daily_goal_minutes if user else 30
            act = DailyActivity(
                id=uuid.uuid4(),
                user_id=user_id,
                activity_date=act_date,
                minutes_practiced=0,
                problems_attempted=0,
                problems_solved=0,
                mock_tests_completed=0,
                xp_earned=0,
                goal_minutes=goal_mins,
                goal_completed=False,
            )
            db.add(act)
            await db.flush()

        return act

    @staticmethod
    async def award_xp(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: int,
        reason: str,
        reference_type: str,
        reference_id: str,
    ) -> int:
        """Awards XP idempotently. Returns amount awarded (0 if duplicate)."""
        if amount <= 0:
            return 0

        # Check idempotency constraint
        check_stmt = select(XPTransaction).where(
            and_(
                XPTransaction.user_id == user_id,
                XPTransaction.reason == reason,
                XPTransaction.reference_type == reference_type,
                XPTransaction.reference_id == str(reference_id),
            )
        )
        existing = (await db.execute(check_stmt)).scalar_one_or_none()
        if existing:
            return 0

        # Record XP Transaction
        tx = XPTransaction(
            id=uuid.uuid4(),
            user_id=user_id,
            amount=amount,
            reason=reason,
            reference_type=reference_type,
            reference_id=str(reference_id),
        )
        db.add(tx)

        # Update User Gamification Profile
        profile = await GamificationService.get_or_create_profile(db, user_id)
        profile.total_xp += amount
        lvl, _, _, _ = calculate_level_from_xp(profile.total_xp)
        profile.current_level = lvl

        # Update Daily Activity XP
        today_act = await GamificationService.get_or_create_daily_activity(db, user_id)
        today_act.xp_earned += amount

        await db.flush()
        return amount

    @staticmethod
    async def update_streak(db: AsyncSession, user_id: uuid.UUID) -> int:
        """Updates user's streak based on qualifying activity date. Returns current_streak."""
        today_date = date.today()
        profile = await GamificationService.get_or_create_profile(db, user_id)

        if profile.last_activity_date == today_date:
            # Already performed qualifying activity today
            return profile.current_streak

        yesterday = today_date - timedelta(days=1)
        if profile.last_activity_date == yesterday:
            profile.current_streak += 1
        else:
            profile.current_streak = 1

        profile.last_activity_date = today_date
        profile.longest_streak = max(profile.longest_streak, profile.current_streak)
        await db.flush()

        # Check streak milestone awards
        milestones = {
            3: (25, "STREAK_MILESTONE_3"),
            7: (75, "STREAK_MILESTONE_7"),
            14: (150, "STREAK_MILESTONE_14"),
            30: (300, "STREAK_MILESTONE_30"),
            60: (500, "STREAK_MILESTONE_60"),
            90: (1000, "STREAK_MILESTONE_90"),
        }

        if profile.current_streak in milestones:
            xp_reward, reason = milestones[profile.current_streak]
            await GamificationService.award_xp(
                db=db,
                user_id=user_id,
                amount=xp_reward,
                reason=reason,
                reference_type="streak",
                reference_id=f"streak_{profile.current_streak}_days",
            )

        return profile.current_streak

    @staticmethod
    async def check_daily_goal_completion(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """Checks if today's daily goal is newly completed."""
        act = await GamificationService.get_or_create_daily_activity(db, user_id)
        if not act.goal_completed and act.minutes_practiced >= act.goal_minutes:
            act.goal_completed = True
            await db.flush()

            await GamificationService.award_xp(
                db=db,
                user_id=user_id,
                amount=25,
                reason="DAILY_GOAL",
                reference_type="daily_goal",
                reference_id=act.activity_date.isoformat(),
            )
            return True
        return act.goal_completed

    @staticmethod
    async def evaluate_badges(db: AsyncSession, user_id: uuid.UUID) -> List[Badge]:
        """ централизованная Centralized badge evaluation engine. Returns list of newly awarded badges."""
        profile = await GamificationService.get_or_create_profile(db, user_id)

        # Get existing unlocked badge IDs
        unlocked_stmt = select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
        unlocked_ids = set((await db.execute(unlocked_stmt)).scalars().all())

        # Load all active badges
        all_badges = (await db.execute(select(Badge).where(Badge.is_active == True))).scalars().all()

        # Gather metrics
        solved_count_stmt = select(func.count(UserProblemProgress.id)).where(
            and_(UserProblemProgress.user_id == user_id, UserProblemProgress.status == "SOLVED")
        )
        solved_count = (await db.execute(solved_count_stmt)).scalar() or 0

        hard_count_stmt = (
            select(func.count(UserProblemProgress.id))
            .join(Problem, UserProblemProgress.problem_id == Problem.id)
            .where(
                and_(
                    UserProblemProgress.user_id == user_id,
                    UserProblemProgress.status == "SOLVED",
                    Problem.difficulty == DifficultyLevel.HARD,
                )
            )
        )
        hard_count = (await db.execute(hard_count_stmt)).scalar() or 0

        mocks_count_stmt = select(func.count(UserMockTest.id)).where(
            and_(
                UserMockTest.user_id == user_id,
                or_(UserMockTest.status == "SUBMITTED", UserMockTest.status == "AUTO_SUBMITTED"),
            )
        )
        mocks_count = (await db.execute(mocks_count_stmt)).scalar() or 0

        newly_awarded = []

        for b in all_badges:
            if b.id in unlocked_ids:
                continue

            should_unlock = False
            if b.slug == "first-steps" and solved_count >= 1:
                should_unlock = True
            elif b.slug == "getting-started" and solved_count >= 5:
                should_unlock = True
            elif b.slug == "problem-solver" and solved_count >= 25:
                should_unlock = True
            elif b.slug == "code-warrior" and solved_count >= 50:
                should_unlock = True
            elif b.slug == "centurion" and solved_count >= 100:
                should_unlock = True
            elif b.slug == "week-warrior" and profile.current_streak >= 7:
                should_unlock = True
            elif b.slug == "consistent-coder" and profile.current_streak >= 30:
                should_unlock = True
            elif b.slug == "hard-mode" and hard_count >= 10:
                should_unlock = True
            elif b.slug == "mock-ready" and mocks_count >= 5:
                should_unlock = True

            if should_unlock:
                ub = UserBadge(id=uuid.uuid4(), user_id=user_id, badge_id=b.id)
                db.add(ub)
                newly_awarded.append(b)

                # Award Badge XP
                await GamificationService.award_xp(
                    db=db,
                    user_id=user_id,
                    amount=b.xp_reward,
                    reason=f"BADGE_{b.slug.upper().replace('-', '_')}",
                    reference_type="badge",
                    reference_id=b.slug,
                )

        if newly_awarded:
            await db.flush()

        return newly_awarded

    @staticmethod
    async def process_problem_solve(
        db: AsyncSession, user_id: uuid.UUID, problem: Problem, is_first_solve: bool
    ):
        """Processes problem solve event and awards XP, updates daily activity & streak."""
        if not is_first_solve:
            return

        # Determine XP reward by difficulty
        xp_map = {
            DifficultyLevel.EASY: 10,
            DifficultyLevel.MEDIUM: 20,
            DifficultyLevel.HARD: 40,
        }
        xp_reward = xp_map.get(problem.difficulty, 10)
        reason = f"SOLVED_{problem.difficulty.value}"

        await GamificationService.award_xp(
            db=db,
            user_id=user_id,
            amount=xp_reward,
            reason=reason,
            reference_type="problem",
            reference_id=str(problem.id),
        )

        # Update Daily Activity
        act = await GamificationService.get_or_create_daily_activity(db, user_id)
        act.problems_solved += 1
        act.minutes_practiced += 15

        # Update Streak, Daily Goal & Badges
        await GamificationService.update_streak(db, user_id)
        await GamificationService.check_daily_goal_completion(db, user_id)
        await GamificationService.evaluate_badges(db, user_id)

    @staticmethod
    async def process_mock_completion(
        db: AsyncSession, user_id: uuid.UUID, session: UserMockTest, mock: MockTest
    ):
        """Processes mock completion event and awards XP."""
        # Determine XP reward by duration/type
        if mock.duration_minutes <= 35:
            xp_reward = 20
        elif mock.duration_minutes <= 65:
            xp_reward = 35
        else:
            xp_reward = 50

        await GamificationService.award_xp(
            db=db,
            user_id=user_id,
            amount=xp_reward,
            reason="MOCK_TEST_COMPLETED",
            reference_type="mock_test",
            reference_id=str(session.id),
        )

        # Update Daily Activity
        act = await GamificationService.get_or_create_daily_activity(db, user_id)
        act.mock_tests_completed += 1
        act.minutes_practiced += mock.duration_minutes

        # Update Streak, Daily Goal & Badges
        await GamificationService.update_streak(db, user_id)
        await GamificationService.check_daily_goal_completion(db, user_id)
        await GamificationService.evaluate_badges(db, user_id)

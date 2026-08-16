import logging
from typing import List, Optional
from datetime import datetime, timezone, date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.gamification import UserGamification, XPTransaction, DailyActivity
from app.schemas.gamification import LeaderboardResponse, LeaderboardItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=LeaderboardResponse)
async def get_weekly_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves current week's competitive leaderboard of opted-in candidates."""
    # Current week window (Monday 00:00 to Sunday 23:59 UTC)
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())

    # Query weekly XP per opted-in user
    opted_in_stmt = select(UserGamification).where(UserGamification.leaderboard_opt_in == True)
    profiles = (await db.execute(opted_in_stmt)).scalars().all()

    leaderboard_data = []

    for p in profiles:
        # Sum XP earned this week
        weekly_xp_stmt = select(func.coalesce(func.sum(DailyActivity.xp_earned), 0)).where(
            and_(
                DailyActivity.user_id == p.user_id,
                DailyActivity.activity_date >= start_of_week,
            )
        )
        weekly_xp = (await db.execute(weekly_xp_stmt)).scalar() or 0

        display_name = p.display_name or f"Candidate_{str(p.user_id)[:6]}"

        leaderboard_data.append({
            "user_id": str(p.user_id),
            "display_name": display_name,
            "level": p.current_level,
            "weekly_xp": weekly_xp,
            "total_xp": p.total_xp,
            "is_current_user": p.user_id == current_user.id,
        })

    # Sort deterministically: weekly_xp DESC, total_xp DESC, display_name ASC
    leaderboard_data.sort(key=lambda x: (-x["weekly_xp"], -x["total_xp"], x["display_name"]))

    items = []
    user_rank = None

    for idx, item in enumerate(leaderboard_data[:limit]):
        rank = idx + 1
        is_me = item["is_current_user"]
        if is_me:
            user_rank = rank

        items.append(
            LeaderboardItem(
                rank=rank,
                user_id=item["user_id"],
                display_name=item["display_name"],
                level=item["level"],
                weekly_xp=item["weekly_xp"],
                total_xp=item["total_xp"],
                is_current_user=is_me,
            )
        )

    # If current user is opted-in but not in top N, find exact rank
    if user_rank is None:
        for idx, item in enumerate(leaderboard_data):
            if item["is_current_user"]:
                user_rank = idx + 1
                break

    return LeaderboardResponse(
        items=items,
        user_rank=user_rank,
        period=f"Week of {start_of_week.strftime('%b %d, %Y')}",
    )

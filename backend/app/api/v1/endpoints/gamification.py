import math
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone, date, timedelta
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.gamification import (
    UserGamification,
    XPTransaction,
    DailyActivity,
    Badge,
    UserBadge,
)
from app.schemas.gamification import (
    UserGamificationResponse,
    DailyActivityResponse,
    BadgeItem,
    XPTransactionItem,
    XPTransactionPaginatedResponse,
    GamificationPreferencesUpdate,
)
from app.services.gamification import (
    GamificationService,
    calculate_level_from_xp,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserGamificationResponse)
async def get_my_gamification_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves current user's XP, level, streak, daily goal, and badge summary."""
    profile = await GamificationService.get_or_create_profile(db, current_user.id)
    today_act = await GamificationService.get_or_create_daily_activity(db, current_user.id)
    await GamificationService.evaluate_badges(db, current_user.id)

    lvl, cur_base, next_base, progress_pct = calculate_level_from_xp(profile.total_xp)

    tot_badges_count = (await db.execute(select(func.count(Badge.id)).where(Badge.is_active == True))).scalar() or 0
    unlocked_count = (await db.execute(select(func.count(UserBadge.id)).where(UserBadge.user_id == current_user.id))).scalar() or 0

    return UserGamificationResponse(
        user_id=current_user.id,
        total_xp=profile.total_xp,
        current_level=lvl,
        xp_for_current_level=cur_base,
        xp_for_next_level=next_base,
        level_progress_pct=progress_pct,
        current_streak=profile.current_streak,
        longest_streak=profile.longest_streak,
        last_activity_date=profile.last_activity_date,
        leaderboard_opt_in=profile.leaderboard_opt_in,
        display_name=profile.display_name,
        today_activity=DailyActivityResponse.model_validate(today_act),
        total_badges=tot_badges_count,
        unlocked_badges_count=unlocked_count,
    )


@router.patch("/preferences")
async def update_gamification_preferences(
    body: GamificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates user leaderboard opt-in status and public display name."""
    profile = await GamificationService.get_or_create_profile(db, current_user.id)

    if body.leaderboard_opt_in is not None:
        profile.leaderboard_opt_in = body.leaderboard_opt_in
    if body.display_name is not None:
        profile.display_name = body.display_name

    await db.commit()
    return {"message": "Preferences updated successfully", "leaderboard_opt_in": profile.leaderboard_opt_in, "display_name": profile.display_name}


@router.get("/badges", response_model=List[BadgeItem])
async def list_user_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves list of all platform badges with user unlock status."""
    await GamificationService.evaluate_badges(db, current_user.id)

    # Get user unlocked badges
    unlocked_stmt = select(UserBadge).where(UserBadge.user_id == current_user.id)
    unlocked_records = (await db.execute(unlocked_stmt)).scalars().all()
    unlocked_map = {ub.badge_id: ub.awarded_at for ub in unlocked_records}

    # Fetch all badges
    all_badges = (await db.execute(select(Badge).where(Badge.is_active == True).order_by(Badge.xp_reward.asc()))).scalars().all()

    items = []
    for b in all_badges:
        is_unlocked = b.id in unlocked_map
        items.append(
            BadgeItem(
                id=b.id,
                slug=b.slug,
                name=b.name,
                description=b.description,
                category=b.category,
                icon_name=b.icon_name,
                xp_reward=b.xp_reward,
                is_unlocked=is_unlocked,
                awarded_at=unlocked_map.get(b.id),
            )
        )

    return items


@router.get("/xp-history", response_model=XPTransactionPaginatedResponse)
async def get_xp_transaction_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves user's auditable XP transaction ledger."""
    base_stmt = select(XPTransaction).where(XPTransaction.user_id == current_user.id)
    count_stmt = select(func.count(XPTransaction.id)).where(XPTransaction.user_id == current_user.id)

    total = (await db.execute(count_stmt)).scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    query = base_stmt.order_by(XPTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    txs = (await db.execute(query)).scalars().all()

    items = [
        XPTransactionItem(
            id=tx.id,
            amount=tx.amount,
            reason=tx.reason,
            reference_type=tx.reference_type,
            reference_id=tx.reference_id,
            created_at=tx.created_at,
        )
        for tx in txs
    ]

    return XPTransactionPaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

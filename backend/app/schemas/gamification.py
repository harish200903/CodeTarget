import uuid
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


class DailyActivityResponse(BaseModel):
    activity_date: date
    minutes_practiced: int
    problems_attempted: int
    problems_solved: int
    mock_tests_completed: int
    xp_earned: int
    goal_minutes: int
    goal_completed: bool

    class Config:
        from_attributes = True


class UserGamificationResponse(BaseModel):
    user_id: uuid.UUID
    total_xp: int
    current_level: int
    xp_for_current_level: int
    xp_for_next_level: int
    level_progress_pct: float
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[date] = None
    leaderboard_opt_in: bool
    display_name: Optional[str] = None
    today_activity: Optional[DailyActivityResponse] = None
    total_badges: int
    unlocked_badges_count: int

    class Config:
        from_attributes = True


class BadgeItem(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    category: str
    icon_name: str
    xp_reward: int
    is_unlocked: bool
    awarded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class XPTransactionItem(BaseModel):
    id: uuid.UUID
    amount: int
    reason: str
    reference_type: str
    reference_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class XPTransactionPaginatedResponse(BaseModel):
    items: List[XPTransactionItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class GamificationPreferencesUpdate(BaseModel):
    leaderboard_opt_in: Optional[bool] = None
    display_name: Optional[str] = Field(None, max_length=100)


class LeaderboardItem(BaseModel):
    rank: int
    user_id: str
    display_name: str
    level: int
    weekly_xp: int
    total_xp: int
    is_current_user: bool = False


class LeaderboardResponse(BaseModel):
    items: List[LeaderboardItem]
    user_rank: Optional[int] = None
    period: str = "This Week"

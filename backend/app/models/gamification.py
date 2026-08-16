import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Text, Integer, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class UserGamification(Base):
    __tablename__ = "user_gamifications"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_xp = Column(Integer, default=0, nullable=False)
    current_level = Column(Integer, default=1, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(Date, nullable=True)
    leaderboard_opt_in = Column(Boolean, default=False, nullable=False)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User")


class XPTransaction(Base):
    __tablename__ = "xp_transactions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False, index=True)
    reference_type = Column(String(50), nullable=False)
    reference_id = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "reason", "reference_type", "reference_id", name="uq_user_xp_reason_ref"),
    )

    user = relationship("User")


class DailyActivity(Base):
    __tablename__ = "daily_activities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date = Column(Date, nullable=False, index=True)
    minutes_practiced = Column(Integer, default=0, nullable=False)
    problems_attempted = Column(Integer, default=0, nullable=False)
    problems_solved = Column(Integer, default=0, nullable=False)
    mock_tests_completed = Column(Integer, default=0, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)
    goal_minutes = Column(Integer, default=30, nullable=False)
    goal_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_user_daily_activity_date"),
    )

    user = relationship("User")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="GENERAL", nullable=False)
    icon_name = Column(String(100), default="award", nullable=False)
    xp_reward = Column(Integer, default=50, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id = Column(GUID, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False, index=True)
    awarded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    user = relationship("User")
    badge = relationship("Badge")

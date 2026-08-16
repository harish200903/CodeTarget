import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class SkillLevel(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    skill_level = Column(SQLEnum(SkillLevel), default=SkillLevel.BEGINNER, nullable=False)
    daily_goal_minutes = Column(Integer, default=30, nullable=False)
    preferred_language = Column(String(20), default="python", nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    target_companies = relationship("UserTargetCompany", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    problem_progress = relationship("UserProblemProgress", back_populates="user", cascade="all, delete-orphan")
    mock_test_attempts = relationship("UserMockTest", back_populates="user", cascade="all, delete-orphan")


class UserTargetCompany(Base):
    __tablename__ = "user_target_companies"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="target_companies")
    company = relationship("Company", back_populates="user_targets")

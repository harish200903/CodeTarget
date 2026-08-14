import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    COMPILE_ERROR = "COMPILE_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class ProgressStatus(str, enum.Enum):
    UNATTEMPTED = "UNATTEMPTED"
    ATTEMPTED = "ATTEMPTED"
    SOLVED = "SOLVED"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(20), nullable=False)  # python, java, cpp
    code = Column(Text, nullable=False)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False, index=True)
    
    execution_time_ms = Column(Integer, nullable=True)
    memory_kb = Column(Integer, nullable=True)
    passed_test_cases = Column(Integer, default=0, nullable=False)
    total_test_cases = Column(Integer, default=0, nullable=False)
    error_output = Column(Text, nullable=True)
    judge0_token = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")


class UserProblemProgress(Base):
    __tablename__ = "user_problem_progress"
    __table_args__ = (
        UniqueConstraint('user_id', 'problem_id', name='uq_user_problem_progress'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(ProgressStatus), default=ProgressStatus.UNATTEMPTED, nullable=False, index=True)
    hints_unlocked = Column(Integer, default=0, nullable=False)
    attempts_count = Column(Integer, default=0, nullable=False)
    personal_notes = Column(Text, nullable=True)
    is_bookmarked = Column(Boolean, default=False, nullable=False)
    
    last_attempted_at = Column(DateTime(timezone=True), nullable=True)
    first_solved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="problem_progress")
    problem = relationship("Problem", back_populates="user_progress")

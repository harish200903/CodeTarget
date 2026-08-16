import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class MockTestStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"


class MockTest(Base):
    __tablename__ = "mock_tests"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=90, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="mock_tests")
    test_problems = relationship("MockTestProblem", back_populates="mock_test", cascade="all, delete-orphan", order_by="MockTestProblem.order_index")
    user_attempts = relationship("UserMockTest", back_populates="mock_test", cascade="all, delete-orphan")


class MockTestProblem(Base):
    __tablename__ = "mock_test_problems"
    __table_args__ = (
        UniqueConstraint('mock_test_id', 'problem_id', name='uq_mock_test_problem'),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    mock_test_id = Column(GUID, ForeignKey("mock_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=1, nullable=False)
    weight_score = Column(Integer, default=100, nullable=False)

    # Relationships
    mock_test = relationship("MockTest", back_populates="test_problems")
    problem = relationship("Problem", back_populates="mock_test_associations")


class UserMockTest(Base):
    __tablename__ = "user_mock_tests"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mock_test_id = Column(GUID, ForeignKey("mock_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(MockTestStatus), default=MockTestStatus.IN_PROGRESS, nullable=False, index=True)
    total_score = Column(Integer, default=0, nullable=False)
    max_possible_score = Column(Integer, default=0, nullable=False)
    
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="mock_test_attempts")
    mock_test = relationship("MockTest", back_populates="user_attempts")
    submissions = relationship("UserMockTestSubmission", back_populates="user_mock_test", cascade="all, delete-orphan")


class UserMockTestSubmission(Base):
    __tablename__ = "user_mock_test_submissions"
    __table_args__ = (
        UniqueConstraint('user_mock_test_id', 'problem_id', name='uq_user_mock_test_problem'),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_mock_test_id = Column(GUID, ForeignKey("user_mock_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(GUID, ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True)
    score_obtained = Column(Integer, default=0, nullable=False)

    # Relationships
    user_mock_test = relationship("UserMockTest", back_populates="submissions")

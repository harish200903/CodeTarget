import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from app.models.base import GUID
from app.models.company import SourceClassification


class DifficultyLevel(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class InterviewRoundType(str, enum.Enum):
    ONLINE_ASSESSMENT = "ONLINE_ASSESSMENT"
    TECHNICAL_SCREEN = "TECHNICAL_SCREEN"
    ONSITE_ROUND = "ONSITE_ROUND"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"


class Topic(Base):
    __tablename__ = "topics"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    problem_associations = relationship("ProblemTopic", back_populates="topic", cascade="all, delete-orphan")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description_markdown = Column(Text, nullable=False)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False, index=True)
    constraints_text = Column(Text, nullable=True)
    starter_code = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    solution_editorial = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    company_associations = relationship("ProblemCompany", back_populates="problem", cascade="all, delete-orphan")
    topic_associations = relationship("ProblemTopic", back_populates="problem", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    hints = relationship("Hint", back_populates="problem", cascade="all, delete-orphan", order_by="Hint.step_number")
    submissions = relationship("Submission", back_populates="problem", cascade="all, delete-orphan")
    user_progress = relationship("UserProblemProgress", back_populates="problem", cascade="all, delete-orphan")
    mock_test_associations = relationship("MockTestProblem", back_populates="problem", cascade="all, delete-orphan")


class ProblemCompany(Base):
    __tablename__ = "problem_companies"
    __table_args__ = (
        UniqueConstraint('problem_id', 'company_id', name='uq_problem_company'),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    frequency_weight = Column(Float, default=1.0, nullable=False)
    recency_window = Column(String(50), default="Last 12 Months", nullable=False)
    round_type = Column(SQLEnum(InterviewRoundType), default=InterviewRoundType.ONLINE_ASSESSMENT, nullable=False)
    source_classification = Column(SQLEnum(SourceClassification), default=SourceClassification.CURATED, nullable=False)

    # Relationships
    problem = relationship("Problem", back_populates="company_associations")
    company = relationship("Company", back_populates="problem_associations")


class ProblemTopic(Base):
    __tablename__ = "problem_topics"
    __table_args__ = (
        UniqueConstraint('problem_id', 'topic_id', name='uq_problem_topic'),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(GUID, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    problem = relationship("Problem", back_populates="topic_associations")
    topic = relationship("Topic", back_populates="problem_associations")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    input_data = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_sample = Column(Boolean, default=False, nullable=False)
    time_limit_ms = Column(Integer, default=2000, nullable=False)
    memory_limit_mb = Column(Integer, default=256, nullable=False)

    # Relationships
    problem = relationship("Problem", back_populates="test_cases")


class Hint(Base):
    __tablename__ = "hints"
    __table_args__ = (
        UniqueConstraint('problem_id', 'step_number', name='uq_problem_hint_step'),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    content_markdown = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)

    # Relationships
    problem = relationship("Problem", back_populates="hints")

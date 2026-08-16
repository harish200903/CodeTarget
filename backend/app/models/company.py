import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class SourceClassification(str, enum.Enum):
    OFFICIAL = "OFFICIAL"
    VERIFIED = "VERIFIED"
    CURATED = "CURATED"
    COMMUNITY_REPORTED = "COMMUNITY_REPORTED"
    PATTERN_BASED = "PATTERN_BASED"


class Company(Base):
    __tablename__ = "companies"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    logo_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    tier = Column(String(50), default="Service & Product Recruiters", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user_targets = relationship("UserTargetCompany", back_populates="company", cascade="all, delete-orphan")
    problem_associations = relationship("ProblemCompany", back_populates="company", cascade="all, delete-orphan")
    mock_tests = relationship("MockTest", back_populates="company", cascade="all, delete-orphan")

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID


class UserAICodeReview(Base):
    """Database model for persisting candidate AI code review reports."""
    __tablename__ = "user_ai_code_reviews"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(20), nullable=False)
    source_code_hash = Column(String(64), nullable=True)
    summary = Column(Text, nullable=False)
    correctness_assessment = Column(Text, nullable=False)
    time_complexity = Column(String(50), nullable=False)
    space_complexity = Column(String(50), nullable=False)
    strengths = Column(JSON, default=list, nullable=False)
    improvements = Column(JSON, default=list, nullable=False)
    bugs = Column(JSON, default=list, nullable=False)
    suggestions = Column(JSON, default=list, nullable=False)
    judge0_status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User")
    problem = relationship("Problem")

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID


class UserAIHint(Base):
    """Database model for persisting candidate unlocked AI hints."""
    __tablename__ = "user_ai_hints"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(GUID, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    hint_level = Column(Integer, nullable=False)
    language = Column(String(20), nullable=False)
    source_code_hash = Column(String(64), nullable=True)
    hint_text = Column(Text, nullable=False)
    focus_concept = Column(String(100), nullable=True)
    should_reveal_solution = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User")
    problem = relationship("Problem")

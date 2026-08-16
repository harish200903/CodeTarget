import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID


class AIUsageLog(Base):
    """Database model for tracking internal AI usage, latency, tokens, and errors."""
    __tablename__ = "ai_usage_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    operation = Column(String(50), nullable=False, index=True)
    model_name = Column(String(50), nullable=False)
    prompt_version = Column(String(20), default="v1", nullable=False)
    input_token_count = Column(Integer, nullable=True)
    output_token_count = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=False)
    is_success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    cache_hit = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User")

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


async def record_audit_log(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Records an administrator audit log event."""
    try:
        log_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        await db.flush()
        return log_entry
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        return None

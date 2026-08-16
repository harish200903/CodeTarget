import hashlib
import json
import logging
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_ai_cache_key(operation: str, payload_data: dict, user_id: Optional[str] = None) -> str:
    """Generates a deterministic SHA256 cache key for AI service requests."""
    serialized = json.dumps(payload_data, sort_keys=True)
    hash_str = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    user_part = f":user:{user_id}" if user_id else ""
    return f"ai_cache:{operation}:{hash_str}{user_part}"


class AICacheService:
    """Reusable Redis caching strategy for deterministic AI responses."""

    def __init__(self, redis_client=None, default_ttl_seconds: int = 86400):
        self.redis_client = redis_client
        self.ttl = default_ttl_seconds

    async def get(self, cache_key: str) -> Optional[dict]:
        if not self.redis_client:
            return None
        try:
            cached_val = await self.redis_client.get(cache_key)
            if cached_val:
                return json.loads(cached_val)
        except Exception as e:
            logger.warning(f"AI Cache lookup failed for key {cache_key}: {e}")
        return None

    async def set(self, cache_key: str, data: dict, ttl_seconds: Optional[int] = None) -> None:
        if not self.redis_client:
            return
        try:
            exp = ttl_seconds or self.ttl
            await self.redis_client.set(cache_key, json.dumps(data), ex=exp)
        except Exception as e:
            logger.warning(f"AI Cache store failed for key {cache_key}: {e}")

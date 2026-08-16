import time
import uuid
import logging
from app.core.config import settings
from app.services.ai.exceptions import AIRateLimitExceeded

logger = logging.getLogger(__name__)


async def check_ai_rate_limit(user_id: uuid.UUID, redis_client) -> None:
    """Enforces Redis sliding-window AI request rate limiting per user."""
    if not redis_client:
        return

    max_limit = settings.AI_RATE_LIMIT_PER_MINUTE
    key = f"rate_limit:ai:{user_id}"
    now = time.time()

    try:
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, now - 60)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, 65)
        res = await pipe.execute()
        
        count = res[1]
        if count >= max_limit:
            raise AIRateLimitExceeded(
                f"AI rate limit exceeded. Maximum {max_limit} requests allowed per minute."
            )
    except AIRateLimitExceeded:
        raise
    except Exception as e:
        logger.warning(f"AI Redis rate limit check bypassed due to connection issue: {e}")

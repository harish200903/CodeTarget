from typing import AsyncGenerator
import redis.asyncio as redis
from app.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency for yielding Redis client connection."""
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()


async def check_redis_health() -> bool:
    """Helper to verify Redis connectivity."""
    try:
        client = redis.Redis(connection_pool=redis_pool)
        pong = await client.ping()
        await client.close()
        return bool(pong)
    except Exception:
        return False

import json
import logging
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user, get_ai_service
from app.models.user import User
from app.schemas.ai import RecommendationListResponse
from app.services.recommendation import RecommendationEngine
from app.services.ai.base import AIService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=RecommendationListResponse)
async def get_personalized_recommendations(
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    ai_service: AIService = Depends(get_ai_service),
):
    """Retrieves personalized practice problem recommendations for authenticated user."""
    cache_key = f"recommendations:user:{current_user.id}:limit:{limit}"

    # 1. Check Redis Cache
    if redis:
        try:
            cached_val = await redis.get(cache_key)
            if cached_val:
                logger.info(f"Recommendation Cache HIT for user {current_user.id}")
                return RecommendationListResponse(**json.loads(cached_val))
        except Exception as e:
            logger.warning(f"Recommendation cache lookup error: {e}")

    # 2. Compute Recommendations using Hybrid Recommendation Engine
    engine = RecommendationEngine(db=db, ai_service=ai_service)
    recommendations = await engine.get_recommendations(user=current_user, limit=limit)

    # 3. Store in Redis Cache (1-hour TTL)
    if redis:
        try:
            await redis.set(cache_key, json.dumps(recommendations.model_dump(mode="json")), ex=3600)
        except Exception as e:
            logger.warning(f"Recommendation cache store error: {e}")

    return recommendations

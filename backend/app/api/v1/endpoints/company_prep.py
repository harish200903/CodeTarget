import json
import uuid
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user, get_ai_service
from app.models.user import User
from app.schemas.company_prep import CompanyPreparationResponse
from app.services.company_prep import CompanyPreparationEngine
from app.services.ai.base import AIService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{company_id}/preparation", response_model=CompanyPreparationResponse)
async def get_company_preparation_overview(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    ai_service: AIService = Depends(get_ai_service),
):
    """Retrieves preparation metrics and topic analytics for a selected target company."""
    cache_key = f"company_prep:user:{current_user.id}:company:{company_id}"

    # 1. Redis Cache Lookup
    if redis:
        try:
            cached_val = await redis.get(cache_key)
            if cached_val:
                logger.info(f"Company Prep Cache HIT for user {current_user.id}, company {company_id}")
                return CompanyPreparationResponse(**json.loads(cached_val))
        except Exception as e:
            logger.warning(f"Company prep cache lookup error: {e}")

    # 2. Compute Preparation Metrics via CompanyPreparationEngine
    engine = CompanyPreparationEngine(db=db, ai_service=ai_service)
    prep_response = await engine.get_company_preparation(user=current_user, company_id=company_id)

    # 3. Store in Redis Cache (1-hour TTL)
    if redis:
        try:
            await redis.set(cache_key, json.dumps(prep_response.model_dump(mode="json")), ex=3600)
        except Exception as e:
            logger.warning(f"Company prep cache store error: {e}")

    return prep_response

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis import check_redis_health
from app.core.config import settings
from app.schemas.health import HealthCheckResponse, ServiceHealth

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, summary="Check System & Service Health")
async def get_health_status(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint verifying:
    1. FastAPI backend server responsiveness
    2. Async PostgreSQL database connectivity
    3. Redis cache & broker connectivity
    """
    services = {}
    overall_status = "ok"

    # 1. Check PostgreSQL Database
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            services["database"] = ServiceHealth(status="healthy", message="PostgreSQL database connected")
        else:
            services["database"] = ServiceHealth(status="unhealthy", message="Unexpected query output")
            overall_status = "degraded"
    except Exception as e:
        services["database"] = ServiceHealth(status="unhealthy", message="Database connection failed")
        overall_status = "degraded"


    # 2. Check Redis Connectivity
    redis_healthy = await check_redis_health()
    if redis_healthy:
        services["redis"] = ServiceHealth(status="healthy", message="Redis broker connected")
    else:
        services["redis"] = ServiceHealth(status="degraded", message="Redis unavailable or unreachable")
        # Redis being down degrades cache but system can respond
        if overall_status == "ok":
            overall_status = "degraded"

    return HealthCheckResponse(
        status=overall_status,
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        services=services
    )

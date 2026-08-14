from datetime import datetime, timezone
from typing import Dict
from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    message: str = Field(..., description="Status message or latency information")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall system health (ok, degraded)")
    app_name: str = Field("CodeTarget", description="Application Name")
    environment: str = Field("development", description="Current environment mode")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    services: Dict[str, ServiceHealth] = Field(...)

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, companies

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users Profile & Onboarding"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, companies, problems, submissions, ai_hints, ai_code_review

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users Profile & Onboarding"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(problems.router, prefix="/problems", tags=["Problems Catalog & Workspace"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions & Execution"])
api_router.include_router(ai_hints.router, prefix="/ai/hints", tags=["AI Progressive Hints"])
api_router.include_router(ai_code_review.router, prefix="/ai/code-review", tags=["AI Code Review"])

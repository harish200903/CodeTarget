from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyOut

router = APIRouter()


@router.get("", response_model=List[CompanyOut], summary="List Available Target Recruiter Companies")
async def list_companies(db: AsyncSession = Depends(get_db)):
    """Retrieve all available target recruiter companies for onboarding selection."""
    stmt = select(Company).order_by(Company.name)
    result = await db.execute(stmt)
    companies = result.scalars().all()
    return [CompanyOut.model_validate(c) for c in companies]

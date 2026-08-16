import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserTargetCompany
from app.models.company import Company
from app.schemas.user import UserOut, OnboardingRequest

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get authenticated user profile and onboarding status."""
    return UserOut.model_validate(current_user)


@router.patch("/onboarding", response_model=UserOut)
async def complete_onboarding(
    onboarding_in: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Persist onboarding selections in a single atomic transaction:
    1. Validate target company IDs exist in database.
    2. Set primary target company (priority = 1) and secondary companies (priority > 1).
    3. Update preferred language, skill level, and daily practice goal.
    4. Mark onboarding_completed = True.
    """
    user_id = current_user.id
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    # 1. Validate company IDs
    target_cids = [uuid.UUID(str(cid)) if isinstance(cid, str) else cid for cid in onboarding_in.target_company_ids]
    primary_cid = uuid.UUID(str(onboarding_in.primary_company_id)) if isinstance(onboarding_in.primary_company_id, str) else onboarding_in.primary_company_id

    stmt = select(Company.id).where(Company.id.in_(target_cids))
    valid_company_ids = (await db.execute(stmt)).scalars().all()
    
    if len(valid_company_ids) != len(set(target_cids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected target companies do not exist"
        )

    # 2. Atomic Database Update
    try:
        # Delete existing target company relations for this user
        del_stmt = select(UserTargetCompany).where(UserTargetCompany.user_id == user_id)
        existing_targets = (await db.execute(del_stmt)).scalars().all()
        for target in existing_targets:
            await db.delete(target)

        await db.flush()

        # Re-create user target company mappings
        for company_id in target_cids:
            priority = 1 if company_id == primary_cid else 2
            new_target = UserTargetCompany(
                user_id=user_id,
                company_id=company_id,
                priority=priority
            )
            db.add(new_target)

        # Update user profile attributes
        current_user.preferred_language = onboarding_in.preferred_language
        current_user.skill_level = onboarding_in.skill_level
        current_user.daily_goal_minutes = onboarding_in.daily_goal_minutes
        current_user.onboarding_completed = True

        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save onboarding selections: {str(e)}"
        )

    # 3. Fetch full updated user profile with target company relationships
    stmt_full = (
        select(User)
        .where(User.id == user_id)
        .execution_options(populate_existing=True)
        .options(
            selectinload(User.target_companies).selectinload(UserTargetCompany.company)
        )
    )
    updated_user = (await db.execute(stmt_full)).scalar_one()

    return UserOut.model_validate(updated_user)

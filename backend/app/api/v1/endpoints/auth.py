import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.models.user import User, UserTargetCompany
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserOut

router = APIRouter()

COOKIE_NAME = "refreshtoken"


def set_refresh_cookie(response: Response, refresh_token: str):
    """Set HttpOnly, SameSite cookie for long-lived refresh token."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        path="/"
    )


async def get_user_with_relations(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Fetch user along with target company relations."""
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.target_companies).selectinload(UserTargetCompany.company)
        )
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account."""
    stmt = select(User).where(User.email == user_in.email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )

    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        onboarding_completed=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    full_user = await get_user_with_relations(db, user.id)

    access_token = create_access_token(data={"sub": str(full_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(full_user.id)})

    set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(full_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_in: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user with email and password."""
    stmt = select(User).where(User.email == user_in.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password"
        )

    full_user = await get_user_with_relations(db, user.id)

    access_token = create_access_token(data={"sub": str(full_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(full_user.id)})

    set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(full_user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Rotate refresh token and issue new short-lived access token."""
    refresh_token = request.cookies.get(COOKIE_NAME)
    if not refresh_token:
        # Fallback to Authorization header if provided
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ")[1]

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )

    full_user = await get_user_with_relations(db, user_id)

    new_access_token = create_access_token(data={"sub": str(full_user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(full_user.id)})

    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        user=UserOut.model_validate(full_user)
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout current session by clearing refresh token cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/", samesite="lax")
    return {"message": "Successfully logged out"}

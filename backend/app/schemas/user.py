import uuid
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from app.models.user import UserRole, SkillLevel
from app.schemas.company import CompanyOut


class UserTargetCompanyOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    priority: int
    company: CompanyOut

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("full_name")
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty or blank")
        return v

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: UserRole
    skill_level: SkillLevel
    daily_goal_minutes: int
    preferred_language: str
    onboarding_completed: bool
    target_companies: List[UserTargetCompanyOut] = []

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class OnboardingRequest(BaseModel):
    target_company_ids: List[uuid.UUID] = Field(..., min_length=1)
    primary_company_id: uuid.UUID
    preferred_language: str = Field(..., pattern="^(python|java|cpp)$")
    skill_level: SkillLevel
    daily_goal_minutes: int = Field(..., ge=15, le=180)

    @model_validator(mode="after")
    def validate_primary_company(self):
        if self.primary_company_id not in self.target_company_ids:
            raise ValueError("Primary target company must be one of the selected target companies")
        return self

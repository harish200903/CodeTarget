import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    tier: str

    model_config = ConfigDict(from_attributes=True)

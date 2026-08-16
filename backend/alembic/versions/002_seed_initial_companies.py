"""Seed initial 10 recruiter companies

Revision ID: 002_seed_initial_companies
Revises: 001_initial_schema
Create Date: 2026-08-14 21:30:00.000000

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = '002_seed_initial_companies'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INITIAL_COMPANIES = [
    {
        "id": uuid.uuid4(),
        "name": "TCS",
        "slug": "tcs",
        "description": "Tata Consultancy Services - Global IT services & recruitment giant.",
        "tier": "Service & Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Cognizant",
        "slug": "cognizant",
        "description": "Cognizant Technology Solutions - IT services and software product engineering.",
        "tier": "Service & Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Infosys",
        "slug": "infosys",
        "description": "Infosys Limited - Global leader in next-generation digital services and consulting.",
        "tier": "Service & Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Accenture",
        "slug": "accenture",
        "description": "Accenture PLC - Leading professional services and technology consulting firm.",
        "tier": "Service & Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Wipro",
        "slug": "wipro",
        "description": "Wipro Limited - Global information technology and consulting services company.",
        "tier": "Service & Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Deloitte",
        "slug": "deloitte",
        "description": "Deloitte - Multinational professional services network and tech advisory.",
        "tier": "Consulting & Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Capgemini",
        "slug": "capgemini",
        "description": "Capgemini - Global leader in partnering with companies to transform and manage their business.",
        "tier": "Service & Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Zoho",
        "slug": "zoho",
        "description": "Zoho Corporation - Premier software product company building cloud & SaaS solutions.",
        "tier": "Product Recruiters",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Amazon",
        "slug": "amazon",
        "description": "Amazon.com Inc. - E-commerce, cloud computing (AWS), and AI technological giant.",
        "tier": "Top Tech",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "id": uuid.uuid4(),
        "name": "Microsoft",
        "slug": "microsoft",
        "description": "Microsoft Corporation - Global leader in software development, cloud systems, and AI.",
        "tier": "Top Tech",
        "created_at": datetime.now(timezone.utc)
    },
]


def upgrade() -> None:
    companies_table = table(
        'companies',
        column('id', GUID()),
        column('name', sa.String),
        column('slug', sa.String),
        column('description', sa.String),
        column('tier', sa.String),
        column('created_at', sa.DateTime(timezone=True))
    )
    
    op.bulk_insert(companies_table, INITIAL_COMPANIES)


def downgrade() -> None:
    op.execute("DELETE FROM companies WHERE slug IN ('tcs', 'cognizant', 'infosys', 'accenture', 'wipro', 'deloitte', 'capgemini', 'zoho', 'amazon', 'microsoft')")

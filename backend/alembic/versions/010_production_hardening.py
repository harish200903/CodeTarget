"""Add is_active column to problems table and migrate INACTIVE categories

Revision ID: 010_production_hardening
Revises: 009_add_gamification_tables
Create Date: 2026-08-16 18:07:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '010_production_hardening'
down_revision: Union[str, None] = '009_add_gamification_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_active column to problems table
    op.add_column('problems', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.create_index('ix_problems_is_active', 'problems', ['is_active'])

    # 2. Migrate existing INACTIVE categories to is_active = False and restore default category
    op.execute("UPDATE problems SET is_active = 0, category = 'Algorithms' WHERE category = 'INACTIVE'")


def downgrade() -> None:
    op.execute("UPDATE problems SET category = 'INACTIVE' WHERE is_active = 0")
    op.drop_index('ix_problems_is_active', table_name='problems')
    op.drop_column('problems', 'is_active')

"""Create user AI code reviews persistence table

Revision ID: 006_add_user_ai_code_reviews
Revises: 005_add_user_ai_hints
Create Date: 2026-08-16 14:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = '006_add_user_ai_code_reviews'
down_revision: Union[str, None] = '005_add_user_ai_hints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_ai_code_reviews',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('problem_id', GUID(), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('source_code_hash', sa.String(64), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('correctness_assessment', sa.Text(), nullable=False),
        sa.Column('time_complexity', sa.String(50), nullable=False),
        sa.Column('space_complexity', sa.String(50), nullable=False),
        sa.Column('strengths', sa.JSON(), nullable=False),
        sa.Column('improvements', sa.JSON(), nullable=False),
        sa.Column('bugs', sa.JSON(), nullable=False),
        sa.Column('suggestions', sa.JSON(), nullable=False),
        sa.Column('judge0_status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_user_ai_code_reviews_user_id', 'user_ai_code_reviews', ['user_id'])
    op.create_index('ix_user_ai_code_reviews_problem_id', 'user_ai_code_reviews', ['problem_id'])
    op.create_index('ix_user_ai_code_reviews_created_at', 'user_ai_code_reviews', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_user_ai_code_reviews_created_at', table_name='user_ai_code_reviews')
    op.drop_index('ix_user_ai_code_reviews_problem_id', table_name='user_ai_code_reviews')
    op.drop_index('ix_user_ai_code_reviews_user_id', table_name='user_ai_code_reviews')
    op.drop_table('user_ai_code_reviews')

"""Create user AI hints persistence table

Revision ID: 005_add_user_ai_hints
Revises: 004_add_ai_usage_logs
Create Date: 2026-08-16 14:44:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_add_user_ai_hints'
down_revision: Union[str, None] = '004_add_ai_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_ai_hints',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('problem_id', sa.String(36), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hint_level', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('source_code_hash', sa.String(64), nullable=True),
        sa.Column('hint_text', sa.Text(), nullable=False),
        sa.Column('focus_concept', sa.String(100), nullable=True),
        sa.Column('should_reveal_solution', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_user_ai_hints_user_id', 'user_ai_hints', ['user_id'])
    op.create_index('ix_user_ai_hints_problem_id', 'user_ai_hints', ['problem_id'])
    op.create_index('ix_user_ai_hints_created_at', 'user_ai_hints', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_user_ai_hints_created_at', table_name='user_ai_hints')
    op.drop_index('ix_user_ai_hints_problem_id', table_name='user_ai_hints')
    op.drop_index('ix_user_ai_hints_user_id', table_name='user_ai_hints')
    op.drop_table('user_ai_hints')

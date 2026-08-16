"""Create AI usage logs tracking table

Revision ID: 004_add_ai_usage_logs
Revises: 003_seed_topics_and_problems
Create Date: 2026-08-16 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = '004_add_ai_usage_logs'
down_revision: Union[str, None] = '003_seed_topics_and_problems'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_usage_logs',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(50), nullable=False),
        sa.Column('prompt_version', sa.String(20), server_default='v1', nullable=False),
        sa.Column('input_token_count', sa.Integer(), nullable=True),
        sa.Column('output_token_count', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('is_success', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_ai_usage_logs_user_id', 'ai_usage_logs', ['user_id'])
    op.create_index('ix_ai_usage_logs_operation', 'ai_usage_logs', ['operation'])
    op.create_index('ix_ai_usage_logs_is_success', 'ai_usage_logs', ['is_success'])
    op.create_index('ix_ai_usage_logs_created_at', 'ai_usage_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_ai_usage_logs_created_at', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_is_success', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_operation', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_user_id', table_name='ai_usage_logs')
    op.drop_table('ai_usage_logs')

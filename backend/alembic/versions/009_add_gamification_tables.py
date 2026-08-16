"""Add gamification tables and seed initial badges

Revision ID: 009_add_gamification_tables
Revises: 008_add_audit_logs
Create Date: 2026-08-16 17:47:30.000000

"""
import uuid
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = '009_add_gamification_tables'
down_revision: Union[str, None] = '008_add_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_gamifications
    op.create_table(
        'user_gamifications',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_activity_date', sa.Date(), nullable=True),
        sa.Column('leaderboard_opt_in', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_user_gamifications_user_id', 'user_gamifications', ['user_id'])

    # 2. xp_transactions
    op.create_table(
        'xp_transactions',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(100), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=False),
        sa.Column('reference_id', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'reason', 'reference_type', 'reference_id', name='uq_user_xp_reason_ref'),
    )
    op.create_index('ix_xp_transactions_user_id', 'xp_transactions', ['user_id'])
    op.create_index('ix_xp_transactions_reason', 'xp_transactions', ['reason'])
    op.create_index('ix_xp_transactions_created_at', 'xp_transactions', ['created_at'])

    # 3. daily_activities
    op.create_table(
        'daily_activities',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_date', sa.Date(), nullable=False),
        sa.Column('minutes_practiced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('problems_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('problems_solved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mock_tests_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('xp_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('goal_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('goal_completed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'activity_date', name='uq_user_daily_activity_date'),
    )
    op.create_index('ix_daily_activities_user_id', 'daily_activities', ['user_id'])
    op.create_index('ix_daily_activities_activity_date', 'daily_activities', ['activity_date'])

    # 4. badges
    op.create_table(
        'badges',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='GENERAL'),
        sa.Column('icon_name', sa.String(100), nullable=False, server_default='award'),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
    )
    op.create_index('ix_badges_slug', 'badges', ['slug'])

    # 5. user_badges
    op.create_table(
        'user_badges',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('user_id', GUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_id', GUID(), sa.ForeignKey('badges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('awarded_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])
    op.create_index('ix_user_badges_badge_id', 'user_badges', ['badge_id'])

    # Seed 10 initial badges
    badges_table = sa.table(
        'badges',
        sa.column('id', GUID()),
        sa.column('slug', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('category', sa.String),
        sa.column('icon_name', sa.String),
        sa.column('xp_reward', sa.Integer),
        sa.column('is_active', sa.Boolean),
    )

    op.bulk_insert(
        badges_table,
        [
            {"id": str(uuid.uuid4()), "slug": "first-steps", "name": "First Steps", "description": "Solve your first coding problem.", "category": "MILESTONE", "icon_name": "footprints", "xp_reward": 25, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "getting-started", "name": "Getting Started", "description": "Solve 5 problems.", "category": "MILESTONE", "icon_name": "target", "xp_reward": 50, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "problem-solver", "name": "Problem Solver", "description": "Solve 25 problems.", "category": "MILESTONE", "icon_name": "brain", "xp_reward": 100, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "code-warrior", "name": "Code Warrior", "description": "Solve 50 problems.", "category": "MILESTONE", "icon_name": "sword", "xp_reward": 200, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "centurion", "name": "Centurion", "description": "Solve 100 problems.", "category": "MILESTONE", "icon_name": "crown", "xp_reward": 500, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "week-warrior", "name": "Week Warrior", "description": "Maintain a 7-day streak.", "category": "STREAK", "icon_name": "flame", "xp_reward": 75, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "consistent-coder", "name": "Consistent Coder", "description": "Maintain a 30-day streak.", "category": "STREAK", "icon_name": "zap", "xp_reward": 300, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "hard-mode", "name": "Hard Mode", "description": "Solve 10 Hard problems.", "category": "MASTERY", "icon_name": "shield", "xp_reward": 250, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "mock-ready", "name": "Mock Ready", "description": "Complete 5 mock tests.", "category": "MOCK", "icon_name": "award", "xp_reward": 200, "is_active": True},
            {"id": str(uuid.uuid4()), "slug": "company-ready", "name": "Company Ready", "description": "Reach WELL_PREPARED status for a target company.", "category": "COMPANY", "icon_name": "building", "xp_reward": 500, "is_active": True},
        ]
    )


def downgrade() -> None:
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('daily_activities')
    op.drop_table('xp_transactions')
    op.drop_table('user_gamifications')

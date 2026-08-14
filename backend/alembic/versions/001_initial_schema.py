"""Initial normalized schema for CodeTarget

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-14 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('role', sa.Enum('USER', 'ADMIN', name='userrole'), nullable=False, server_default='USER'),
        sa.Column('skill_level', sa.Enum('BEGINNER', 'INTERMEDIATE', 'ADVANCED', name='skilllevel'), nullable=False, server_default='BEGINNER'),
        sa.Column('daily_goal_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('preferred_language', sa.String(20), nullable=False, server_default='python'),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # 2. Companies
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tier', sa.String(50), nullable=False, server_default='Service & Product Recruiters'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_companies_slug', 'companies', ['slug'])

    # 3. User Target Companies
    op.create_table(
        'user_target_companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_utc_user_id', 'user_target_companies', ['user_id'])
    op.create_index('ix_utc_company_id', 'user_target_companies', ['company_id'])

    # 4. Topics
    op.create_table(
        'topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True)
    )
    op.create_index('ix_topics_slug', 'topics', ['slug'])

    # 5. Problems
    op.create_table(
        'problems',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('description_markdown', sa.Text(), nullable=False),
        sa.Column('difficulty', sa.Enum('EASY', 'MEDIUM', 'HARD', name='difficultylevel'), nullable=False),
        sa.Column('constraints_text', sa.Text(), nullable=True),
        sa.Column('starter_code', postgresql.JSONB(), nullable=False),
        sa.Column('solution_editorial', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_problems_slug', 'problems', ['slug'])
    op.create_index('ix_problems_difficulty', 'problems', ['difficulty'])

    # 6. Problem Companies
    op.create_table(
        'problem_companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('frequency_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('recency_window', sa.String(50), nullable=False, server_default='Last 12 Months'),
        sa.Column('round_type', sa.Enum('ONLINE_ASSESSMENT', 'TECHNICAL_SCREEN', 'ONSITE_ROUND', 'SYSTEM_DESIGN', name='interviewroundtype'), nullable=False, server_default='ONLINE_ASSESSMENT'),
        sa.Column('source_classification', sa.Enum('OFFICIAL', 'VERIFIED', 'CURATED', 'COMMUNITY_REPORTED', 'PATTERN_BASED', name='sourceclassification'), nullable=False, server_default='CURATED'),
        sa.UniqueConstraint('problem_id', 'company_id', name='uq_problem_company')
    )

    # 7. Problem Topics
    op.create_table(
        'problem_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('problem_id', 'topic_id', name='uq_problem_topic')
    )

    # 8. Test Cases
    op.create_table(
        'test_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('is_sample', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('time_limit_ms', sa.Integer(), nullable=False, server_default='2000'),
        sa.Column('memory_limit_mb', sa.Integer(), nullable=False, server_default='256')
    )

    # 9. Hints
    op.create_table(
        'hints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('code_snippet', sa.Text(), nullable=True),
        sa.UniqueConstraint('problem_id', 'step_number', name='uq_problem_hint_step')
    )

    # 10. Submissions
    op.create_table(
        'submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'QUEUED', 'RUNNING', 'ACCEPTED', 'WRONG_ANSWER', 'TIME_LIMIT_EXCEEDED', 'MEMORY_LIMIT_EXCEEDED', 'RUNTIME_ERROR', 'COMPILE_ERROR', 'SYSTEM_ERROR', name='submissionstatus'), nullable=False, server_default='PENDING'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('memory_kb', sa.Integer(), nullable=True),
        sa.Column('passed_test_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_test_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_output', sa.Text(), nullable=True),
        sa.Column('judge0_token', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 11. User Problem Progress
    op.create_table(
        'user_problem_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.Enum('UNATTEMPTED', 'ATTEMPTED', 'SOLVED', name='progressstatus'), nullable=False, server_default='UNATTEMPTED'),
        sa.Column('hints_unlocked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attempts_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('personal_notes', sa.Text(), nullable=True),
        sa.Column('is_bookmarked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_attempted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_solved_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('user_id', 'problem_id', name='uq_user_problem_progress')
    )

    # 12. Mock Tests
    op.create_table(
        'mock_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 13. Mock Test Problems
    op.create_table(
        'mock_test_problems',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mock_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mock_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('weight_score', sa.Integer(), nullable=False, server_default='100'),
        sa.UniqueConstraint('mock_test_id', 'problem_id', name='uq_mock_test_problem')
    )

    # 14. User Mock Tests
    op.create_table(
        'user_mock_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mock_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mock_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'TIMED_OUT', name='mockteststatus'), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('total_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_possible_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )

    # 15. User Mock Test Submissions
    op.create_table(
        'user_mock_test_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_mock_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_mock_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('score_obtained', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('user_mock_test_id', 'problem_id', name='uq_user_mock_test_problem')
    )


def downgrade() -> None:
    op.drop_table('user_mock_test_submissions')
    op.drop_table('user_mock_tests')
    op.drop_table('mock_test_problems')
    op.drop_table('mock_tests')
    op.drop_table('user_problem_progress')
    op.drop_table('submissions')
    op.drop_table('hints')
    op.drop_table('test_cases')
    op.drop_table('problem_topics')
    op.drop_table('problem_companies')
    op.drop_table('problems')
    op.drop_table('topics')
    op.drop_table('user_target_companies')
    op.drop_table('companies')
    op.drop_table('users')

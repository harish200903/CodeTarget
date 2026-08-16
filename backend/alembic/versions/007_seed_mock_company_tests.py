"""Seed mock company coding test configurations

Revision ID: 007_seed_mock_company_tests
Revises: 006_add_user_ai_code_reviews
Create Date: 2026-08-16 16:04:00.000000

"""
import uuid
from typing import Sequence, Union
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select

# revision identifiers, used by Alembic.
revision: str = '007_seed_mock_company_tests'
down_revision: Union[str, None] = '006_add_user_ai_code_reviews'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

companies_table = table(
    'companies',
    column('id', sa.String),
    column('name', sa.String),
    column('slug', sa.String)
)

problems_table = table(
    'problems',
    column('id', sa.String),
    column('title', sa.String),
    column('difficulty', sa.String)
)

problem_companies_table = table(
    'problem_companies',
    column('problem_id', sa.String),
    column('company_id', sa.String)
)

mock_tests_table = table(
    'mock_tests',
    column('id', sa.String),
    column('company_id', sa.String),
    column('title', sa.String),
    column('description', sa.String),
    column('duration_minutes', sa.Integer),
    column('created_at', sa.DateTime(timezone=True))
)

mock_test_problems_table = table(
    'mock_test_problems',
    column('id', sa.String),
    column('mock_test_id', sa.String),
    column('problem_id', sa.String),
    column('order_index', sa.Integer),
    column('weight_score', sa.Integer)
)


def upgrade() -> None:
    conn = op.get_bind()

    # Query all companies
    companies = conn.execute(select(companies_table.c.id, companies_table.c.name, companies_table.c.slug)).fetchall()
    all_problems = conn.execute(select(problems_table.c.id, problems_table.c.difficulty)).fetchall()

    if not companies or not all_problems:
        return

    easy_probs = [p.id for p in all_problems if p.difficulty == 'EASY']
    med_probs = [p.id for p in all_problems if p.difficulty == 'MEDIUM']
    hard_probs = [p.id for p in all_problems if p.difficulty == 'HARD']

    # Fallbacks if list is empty
    if not easy_probs: easy_probs = [all_problems[0].id]
    if not med_probs: med_probs = [all_problems[0].id]
    if not hard_probs: hard_probs = [all_problems[-1].id]

    now = datetime.now(timezone.utc)

    for comp in companies:
        comp_id = comp.id
        comp_name = comp.name

        # Query company-linked problems
        comp_prob_stmt = select(problem_companies_table.c.problem_id).where(problem_companies_table.c.company_id == comp_id)
        c_probs = [row[0] for row in conn.execute(comp_prob_stmt).fetchall()]

        # Filter by difficulty or use general pool
        c_easy = [p for p in easy_probs if p in c_probs] or easy_probs
        c_med = [p for p in med_probs if p in c_probs] or med_probs
        c_hard = [p for p in hard_probs if p in c_probs] or hard_probs

        # 1. Quick Mock (30 mins, 2 problems: 1 Easy, 1 Medium)
        q_id = str(uuid.uuid4())
        conn.execute(mock_tests_table.insert().values(
            id=q_id,
            company_id=comp_id,
            title=f"{comp_name}-Style Quick Mock",
            description=f"2 Problems • 30 Minutes. Quick practice simulation tailored for {comp_name} coding round patterns.",
            duration_minutes=30,
            created_at=now
        ))
        conn.execute(mock_test_problems_table.insert().values([
            {'id': str(uuid.uuid4()), 'mock_test_id': q_id, 'problem_id': c_easy[0], 'order_index': 1, 'weight_score': 50},
            {'id': str(uuid.uuid4()), 'mock_test_id': q_id, 'problem_id': c_med[0], 'order_index': 2, 'weight_score': 50},
        ]))

        # 2. Standard Mock (60 mins, 3 problems: 1 Easy, 2 Medium)
        s_id = str(uuid.uuid4())
        p2_med = c_med[1] if len(c_med) > 1 else c_med[0]
        conn.execute(mock_tests_table.insert().values(
            id=s_id,
            company_id=comp_id,
            title=f"{comp_name}-Style Standard Mock",
            description=f"3 Problems • 60 Minutes. Standard assessment simulation for {comp_name} interview rounds.",
            duration_minutes=60,
            created_at=now
        ))
        conn.execute(mock_test_problems_table.insert().values([
            {'id': str(uuid.uuid4()), 'mock_test_id': s_id, 'problem_id': c_easy[0], 'order_index': 1, 'weight_score': 30},
            {'id': str(uuid.uuid4()), 'mock_test_id': s_id, 'problem_id': c_med[0], 'order_index': 2, 'weight_score': 35},
            {'id': str(uuid.uuid4()), 'mock_test_id': s_id, 'problem_id': p2_med, 'order_index': 3, 'weight_score': 35},
        ]))

        # 3. Full Mock (90 mins, 4 problems: 1 Easy, 2 Medium, 1 Hard)
        f_id = str(uuid.uuid4())
        conn.execute(mock_tests_table.insert().values(
            id=f_id,
            company_id=comp_id,
            title=f"{comp_name}-Style Full Assessment Mock",
            description=f"4 Problems • 90 Minutes. Comprehensive full-length coding assessment for {comp_name}.",
            duration_minutes=90,
            created_at=now
        ))
        conn.execute(mock_test_problems_table.insert().values([
            {'id': str(uuid.uuid4()), 'mock_test_id': f_id, 'problem_id': c_easy[0], 'order_index': 1, 'weight_score': 20},
            {'id': str(uuid.uuid4()), 'mock_test_id': f_id, 'problem_id': c_med[0], 'order_index': 2, 'weight_score': 25},
            {'id': str(uuid.uuid4()), 'mock_test_id': f_id, 'problem_id': p2_med, 'order_index': 3, 'weight_score': 25},
            {'id': str(uuid.uuid4()), 'mock_test_id': f_id, 'problem_id': c_hard[0], 'order_index': 4, 'weight_score': 30},
        ]))


def downgrade() -> None:
    op.execute("DELETE FROM mock_test_problems")
    op.execute("DELETE FROM mock_tests")

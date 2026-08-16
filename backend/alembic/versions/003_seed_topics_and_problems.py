"""Seed initial 19 DSA topics and 50 coding problems

Revision ID: 003_seed_topics_and_problems
Revises: 002_seed_initial_companies
Create Date: 2026-08-16 13:00:00.000000

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import JSONB

from app.db.seed_data import DSA_TOPICS, PROBLEMS_DATA

# revision identifiers, used by Alembic.
revision: str = '003_seed_topics_and_problems'
down_revision: Union[str, None] = '002_seed_initial_companies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add category column to problems table if not already present
    with op.batch_alter_table("problems") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(100), server_default="Algorithms", nullable=False))

    conn = op.get_bind()

    # 1. Seed Topics
    topics_table = table(
        'topics',
        column('id', sa.String),
        column('name', sa.String),
        column('slug', sa.String),
        column('description', sa.String)
    )

    topic_id_map = {}
    topic_rows = []
    for t in DSA_TOPICS:
        t_id = str(uuid.uuid4())
        topic_id_map[t["slug"]] = t_id
        topic_rows.append({
            "id": t_id,
            "name": t["name"],
            "slug": t["slug"],
            "description": t["description"]
        })
    
    op.bulk_insert(topics_table, topic_rows)

    # 2. Fetch existing company slug -> id map
    res = conn.execute(sa.text("SELECT id, slug FROM companies"))
    company_id_map = {row.slug: str(row.id) for row in res}

    # 3. Tables for bulk inserts
    problems_table = table(
        'problems',
        column('id', sa.String),
        column('title', sa.String),
        column('slug', sa.String),
        column('description_markdown', sa.String),
        column('difficulty', sa.String),
        column('category', sa.String),
        column('constraints_text', sa.String),
        column('starter_code', JSONB),
        column('solution_editorial', sa.String),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )

    prob_topics_table = table(
        'problem_topics',
        column('id', sa.String),
        column('problem_id', sa.String),
        column('topic_id', sa.String)
    )

    prob_companies_table = table(
        'problem_companies',
        column('id', sa.String),
        column('problem_id', sa.String),
        column('company_id', sa.String),
        column('frequency_weight', sa.Float),
        column('recency_window', sa.String),
        column('round_type', sa.String),
        column('source_classification', sa.String)
    )

    test_cases_table = table(
        'test_cases',
        column('id', sa.String),
        column('problem_id', sa.String),
        column('input_data', sa.String),
        column('expected_output', sa.String),
        column('is_sample', sa.Boolean),
        column('time_limit_ms', sa.Integer),
        column('memory_limit_mb', sa.Integer)
    )

    hints_table = table(
        'hints',
        column('id', sa.String),
        column('problem_id', sa.String),
        column('step_number', sa.Integer),
        column('title', sa.String),
        column('content_markdown', sa.String),
        column('code_snippet', sa.String)
    )

    now = datetime.now(timezone.utc)
    problem_rows = []
    prob_topic_rows = []
    prob_company_rows = []
    test_case_rows = []
    hint_rows = []

    for prob in PROBLEMS_DATA:
        p_id = str(uuid.uuid4())
        problem_rows.append({
            "id": p_id,
            "title": prob["title"],
            "slug": prob["slug"],
            "description_markdown": prob["description_markdown"],
            "difficulty": prob["difficulty"],
            "category": prob["category"],
            "constraints_text": prob["constraints_text"],
            "starter_code": prob["starter_code"],
            "solution_editorial": prob["solution_editorial"],
            "created_at": now,
            "updated_at": now
        })

        # Problem - Topic junction rows
        for t_slug in prob["topics"]:
            if t_slug in topic_id_map:
                prob_topic_rows.append({
                    "id": str(uuid.uuid4()),
                    "problem_id": p_id,
                    "topic_id": topic_id_map[t_slug]
                })

        # Problem - Company junction rows
        for c_slug in prob["companies"]:
            if c_slug in company_id_map:
                prob_company_rows.append({
                    "id": str(uuid.uuid4()),
                    "problem_id": p_id,
                    "company_id": company_id_map[c_slug],
                    "frequency_weight": 1.0,
                    "recency_window": "Last 12 Months",
                    "round_type": "ONLINE_ASSESSMENT",
                    "source_classification": "CURATED"
                })

        # Sample Test Cases
        for tc in prob["sample_test_cases"]:
            test_case_rows.append({
                "id": str(uuid.uuid4()),
                "problem_id": p_id,
                "input_data": tc["input"],
                "expected_output": tc["expected_output"],
                "is_sample": True,
                "time_limit_ms": 2000,
                "memory_limit_mb": 256
            })

        # Hidden Test Cases
        for tc in prob["hidden_test_cases"]:
            test_case_rows.append({
                "id": str(uuid.uuid4()),
                "problem_id": p_id,
                "input_data": tc["input"],
                "expected_output": tc["expected_output"],
                "is_sample": False,
                "time_limit_ms": 2000,
                "memory_limit_mb": 256
            })

        # Progressive Hints
        for h in prob["hints"]:
            hint_rows.append({
                "id": str(uuid.uuid4()),
                "problem_id": p_id,
                "step_number": h["step"],
                "title": h["title"],
                "content_markdown": h["content"],
                "code_snippet": None
            })

    op.bulk_insert(problems_table, problem_rows)
    op.bulk_insert(prob_topics_table, prob_topic_rows)
    op.bulk_insert(prob_companies_table, prob_company_rows)
    op.bulk_insert(test_cases_table, test_case_rows)
    op.bulk_insert(hints_table, hint_rows)


def downgrade() -> None:
    op.execute("DELETE FROM hints")
    op.execute("DELETE FROM test_cases")
    op.execute("DELETE FROM problem_companies")
    op.execute("DELETE FROM problem_topics")
    op.execute("DELETE FROM problems")
    op.execute("DELETE FROM topics")
    with op.batch_alter_table("problems") as batch_op:
        batch_op.drop_column("category")

import math
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, or_

from app.core.database import get_db
from app.api.deps import require_admin_role
from app.models.user import User
from app.models.company import Company
from app.models.problem import Problem, Topic, ProblemCompany, ProblemTopic, TestCase, Hint, DifficultyLevel
from app.models.mock_test import MockTest, MockTestProblem
from app.models.audit import AuditLog
from app.schemas.admin import (
    AdminDashboardSummary,
    AdminCompanyCreateRequest,
    AdminCompanyUpdateRequest,
    AdminTopicCreateRequest,
    AdminTopicUpdateRequest,
    AdminProblemCreateRequest,
    AdminProblemUpdateRequest,
    AdminTestCaseCreateRequest,
    AdminTestCaseUpdateRequest,
    AdminHintCreateRequest,
    AdminHintUpdateRequest,
    AdminMockTestCreateRequest,
    AdminMockTestUpdateRequest,
    AuditLogItem,
    AuditLogPaginatedResponse,
)
from app.services.audit import record_audit_log

logger = logging.getLogger(__name__)

router = APIRouter()


# 1. Admin Dashboard Summary
@router.get("/dashboard", response_model=AdminDashboardSummary)
async def get_admin_dashboard_summary(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves content-management summary counts for the admin overview dashboard."""
    comp_count = (await db.execute(select(func.count(Company.id)))).scalar() or 0
    top_count = (await db.execute(select(func.count(Topic.id)))).scalar() or 0
    prob_count = (await db.execute(select(func.count(Problem.id)))).scalar() or 0

    # Active problems
    act_prob_stmt = select(func.count(Problem.id)).where(
        or_(Problem.category != "INACTIVE", Problem.category == None)
    )
    act_prob_count = (await db.execute(act_prob_stmt)).scalar() or 0

    mock_count = (await db.execute(select(func.count(MockTest.id)))).scalar() or 0
    tc_count = (await db.execute(select(func.count(TestCase.id)))).scalar() or 0
    hint_count = (await db.execute(select(func.count(Hint.id)))).scalar() or 0

    return AdminDashboardSummary(
        companies_count=comp_count,
        topics_count=top_count,
        problems_count=prob_count,
        active_problems_count=act_prob_count,
        mock_tests_count=mock_count,
        total_test_cases=tc_count,
        total_hints=hint_count,
    )


# 2. Company Management
@router.get("/companies")
async def list_companies_admin(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Lists all companies with associated problem counts."""
    stmt = select(Company).options(selectinload(Company.problem_associations))
    res = await db.execute(stmt)
    companies = res.scalars().all()

    items = []
    for c in companies:
        items.append({
            "id": str(c.id),
            "name": c.name,
            "slug": c.slug,
            "tier": c.tier,
            "description": c.description,
            "logo_url": c.logo_url,
            "problem_count": len(c.problem_associations) if c.problem_associations else 0,
        })
    return items


@router.post("/companies", status_code=status.HTTP_201_CREATED)
async def create_company_admin(
    body: AdminCompanyCreateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new target company."""
    # Check unique slug
    existing = (await db.execute(select(Company).where(Company.slug == body.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company slug already exists.")

    company = Company(
        id=uuid.uuid4(),
        name=body.name,
        slug=body.slug,
        tier=body.tier,
        description=body.description,
        logo_url=body.logo_url,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="CREATE_COMPANY",
        resource_type="company",
        resource_id=str(company.id),
        details={"name": company.name, "slug": company.slug},
    )
    await db.commit()

    return {"id": str(company.id), "name": company.name, "slug": company.slug}


@router.patch("/companies/{company_id}")
async def update_company_admin(
    company_id: uuid.UUID,
    body: AdminCompanyUpdateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Updates target company metadata."""
    stmt = select(Company).where(Company.id == company_id)
    company = (await db.execute(stmt)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    if body.slug and body.slug != company.slug:
        dup = (await db.execute(select(Company).where(Company.slug == body.slug))).scalar_one_or_none()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company slug already exists.")
        company.slug = body.slug

    if body.name is not None: company.name = body.name
    if body.tier is not None: company.tier = body.tier
    if body.description is not None: company.description = body.description
    if body.logo_url is not None: company.logo_url = body.logo_url

    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="UPDATE_COMPANY",
        resource_type="company",
        resource_id=str(company.id),
        details={"name": company.name, "slug": company.slug},
    )
    await db.commit()

    return {"message": "Company updated successfully", "id": str(company.id)}


# 3. Topic Management
@router.get("/topics")
async def list_topics_admin(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Lists all DSA topics with problem counts."""
    stmt = select(Topic).options(selectinload(Topic.problem_associations))
    res = await db.execute(stmt)
    topics = res.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "description": t.description,
            "problem_count": len(t.problem_associations) if t.problem_associations else 0,
        }
        for t in topics
    ]


@router.post("/topics", status_code=status.HTTP_201_CREATED)
async def create_topic_admin(
    body: AdminTopicCreateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new DSA topic."""
    existing = (await db.execute(select(Topic).where(Topic.slug == body.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic slug already exists.")

    topic = Topic(
        id=uuid.uuid4(),
        name=body.name,
        slug=body.slug,
        description=body.description,
    )
    db.add(topic)
    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="CREATE_TOPIC",
        resource_type="topic",
        resource_id=str(topic.id),
        details={"name": topic.name, "slug": topic.slug},
    )
    await db.commit()

    return {"id": str(topic.id), "name": topic.name, "slug": topic.slug}


@router.patch("/topics/{topic_id}")
async def update_topic_admin(
    topic_id: uuid.UUID,
    body: AdminTopicUpdateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Updates a DSA topic."""
    topic = (await db.execute(select(Topic).where(Topic.id == topic_id))).scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")

    if body.slug and body.slug != topic.slug:
        dup = (await db.execute(select(Topic).where(Topic.slug == body.slug))).scalar_one_or_none()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic slug already exists.")
        topic.slug = body.slug

    if body.name is not None: topic.name = body.name
    if body.description is not None: topic.description = body.description

    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="UPDATE_TOPIC",
        resource_type="topic",
        resource_id=str(topic.id),
        details={"name": topic.name, "slug": topic.slug},
    )
    await db.commit()

    return {"message": "Topic updated successfully", "id": str(topic.id)}


# 4. Problem Management
@router.get("/problems")
async def list_problems_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Lists problems with filtering for admin content management."""
    base_stmt = select(Problem).options(
        selectinload(Problem.topic_associations).selectinload(ProblemTopic.topic),
        selectinload(Problem.company_associations).selectinload(ProblemCompany.company),
        selectinload(Problem.test_cases),
        selectinload(Problem.hints),
    )

    filters = []
    if search:
        filters.append(Problem.title.ilike(f"%{search}%"))
    if difficulty:
        filters.append(Problem.difficulty == DifficultyLevel[difficulty.upper()])

    if filters:
        base_stmt = base_stmt.where(and_(*filters))

    count_stmt = select(func.count(Problem.id))
    if filters:
        count_stmt = count_stmt.where(and_(*filters))

    total = (await db.execute(count_stmt)).scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    query = base_stmt.order_by(Problem.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    probs = (await db.execute(query)).scalars().all()

    items = []
    for p in probs:
        items.append({
            "id": str(p.id),
            "title": p.title,
            "slug": p.slug,
            "difficulty": p.difficulty.value,
            "category": p.category,
            "is_active": p.category != "INACTIVE",
            "test_cases_count": len(p.test_cases),
            "hints_count": len(p.hints),
            "companies": [pc.company.name for pc in p.company_associations if pc.company],
            "topics": [pt.topic.name for pt in p.topic_associations if pt.topic],
        })

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


@router.post("/problems", status_code=status.HTTP_201_CREATED)
async def create_problem_admin(
    body: AdminProblemCreateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new coding problem with company and topic associations."""
    # Check unique slug
    existing = (await db.execute(select(Problem).where(Problem.slug == body.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Problem slug already exists.")

    try:
        diff_enum = DifficultyLevel[body.difficulty.upper()]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid difficulty level. Must be EASY, MEDIUM, or HARD.")

    prob_id = uuid.uuid4()
    problem = Problem(
        id=prob_id,
        title=body.title,
        slug=body.slug,
        difficulty=diff_enum,
        category=body.category or "Algorithms",
        is_active=body.is_active,
        description_markdown=body.description_markdown,
        constraints_text=body.constraints_text,
        starter_code=body.starter_code or {},
        solution_editorial=body.solution_editorial,
    )

    db.add(problem)
    await db.flush()

    # Company associations
    for c_id in body.company_ids:
        db.add(ProblemCompany(
            id=uuid.uuid4(),
            problem_id=prob_id,
            company_id=c_id,
            frequency_weight=1.0,
            recency_window="Last 12 Months",
            round_type="ONLINE_ASSESSMENT",
            source_classification="CURATED",
        ))

    # Topic associations
    for t_id in body.topic_ids:
        db.add(ProblemTopic(
            id=uuid.uuid4(),
            problem_id=prob_id,
            topic_id=t_id,
        ))

    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="CREATE_PROBLEM",
        resource_type="problem",
        resource_id=str(prob_id),
        details={"title": problem.title, "slug": problem.slug},
    )
    await db.commit()

    return {"id": str(prob_id), "title": problem.title, "slug": problem.slug}


@router.get("/problems/{problem_id}")
async def get_problem_detail_admin(
    problem_id: uuid.UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full admin details for a problem including test cases and hints."""
    stmt = (
        select(Problem)
        .where(Problem.id == problem_id)
        .options(
            selectinload(Problem.topic_associations).selectinload(ProblemTopic.topic),
            selectinload(Problem.company_associations).selectinload(ProblemCompany.company),
            selectinload(Problem.test_cases),
            selectinload(Problem.hints),
        )
    )
    problem = (await db.execute(stmt)).scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")

    return {
        "id": str(problem.id),
        "title": problem.title,
        "slug": problem.slug,
        "difficulty": problem.difficulty.value,
        "category": problem.category,
        "description_markdown": problem.description_markdown,
        "constraints_text": problem.constraints_text,
        "starter_code": problem.starter_code,
        "solution_editorial": problem.solution_editorial,
        "is_active": problem.category != "INACTIVE",
        "company_ids": [str(pc.company_id) for pc in problem.company_associations],
        "topic_ids": [str(pt.topic_id) for pt in problem.topic_associations],
        "test_cases": [
            {
                "id": str(tc.id),
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_sample": tc.is_sample,
                "time_limit_ms": tc.time_limit_ms,
                "memory_limit_mb": tc.memory_limit_mb,
            }
            for tc in problem.test_cases
        ],
        "hints": [
            {
                "id": str(h.id),
                "step_number": h.step_number,
                "title": h.title,
                "content_markdown": h.content_markdown,
            }
            for h in problem.hints
        ],
    }


@router.patch("/problems/{problem_id}")
async def update_problem_admin(
    problem_id: uuid.UUID,
    body: AdminProblemUpdateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Updates a problem and its company/topic associations."""
    stmt = (
        select(Problem)
        .where(Problem.id == problem_id)
        .options(
            selectinload(Problem.company_associations),
            selectinload(Problem.topic_associations),
        )
    )
    problem = (await db.execute(stmt)).scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")

    if body.slug and body.slug != problem.slug:
        dup = (await db.execute(select(Problem).where(Problem.slug == body.slug))).scalar_one_or_none()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Problem slug already exists.")
        problem.slug = body.slug

    if body.title is not None: problem.title = body.title
    if body.difficulty is not None:
        try:
            problem.difficulty = DifficultyLevel[body.difficulty.upper()]
        except KeyError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid difficulty level.")
    if body.category is not None: problem.category = body.category
    if body.is_active is not None: problem.is_active = body.is_active
    if body.description_markdown is not None: problem.description_markdown = body.description_markdown

    if body.constraints_text is not None: problem.constraints_text = body.constraints_text
    if body.starter_code is not None: problem.starter_code = body.starter_code
    if body.solution_editorial is not None: problem.solution_editorial = body.solution_editorial

    # Update company associations
    if body.company_ids is not None:
        for pc in problem.company_associations:
            await db.delete(pc)
        for c_id in body.company_ids:
            db.add(ProblemCompany(
                id=uuid.uuid4(),
                problem_id=problem.id,
                company_id=c_id,
                frequency_weight=1.0,
                recency_window="Last 12 Months",
                round_type="ONLINE_ASSESSMENT",
                source_classification="CURATED",
            ))

    # Update topic associations
    if body.topic_ids is not None:
        for pt in problem.topic_associations:
            await db.delete(pt)
        for t_id in body.topic_ids:
            db.add(ProblemTopic(
                id=uuid.uuid4(),
                problem_id=problem.id,
                topic_id=t_id,
            ))

    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="UPDATE_PROBLEM",
        resource_type="problem",
        resource_id=str(problem.id),
        details={"title": problem.title, "slug": problem.slug},
    )
    await db.commit()

    return {"message": "Problem updated successfully", "id": str(problem.id)}


@router.delete("/problems/{problem_id}")
async def deactivate_problem_admin(
    problem_id: uuid.UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Soft-deactivates a problem to preserve historical candidate submissions."""
    problem = (await db.execute(select(Problem).where(Problem.id == problem_id))).scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")

    problem.is_active = False
    await db.commit()


    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="DEACTIVATE_PROBLEM",
        resource_type="problem",
        resource_id=str(problem.id),
        details={"title": problem.title},
    )
    await db.commit()

    return {"message": "Problem soft-deactivated successfully"}


# 5. Test Case Management
@router.post("/problems/{problem_id}/test-cases", status_code=status.HTTP_201_CREATED)
async def create_test_case_admin(
    problem_id: uuid.UUID,
    body: AdminTestCaseCreateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Creates a public or hidden evaluation test case for a problem."""
    tc = TestCase(
        id=uuid.uuid4(),
        problem_id=problem_id,
        input_data=body.input_data,
        expected_output=body.expected_output,
        is_sample=body.is_sample,
        time_limit_ms=body.time_limit_ms,
        memory_limit_mb=body.memory_limit_mb,
    )
    db.add(tc)
    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="CREATE_TEST_CASE",
        resource_type="test_case",
        resource_id=str(tc.id),
        details={"problem_id": str(problem_id), "is_sample": tc.is_sample},
    )
    await db.commit()

    return {"id": str(tc.id), "is_sample": tc.is_sample}


@router.delete("/test-cases/{test_case_id}")
async def delete_test_case_admin(
    test_case_id: uuid.UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a test case."""
    tc = (await db.execute(select(TestCase).where(TestCase.id == test_case_id))).scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found.")

    prob_id = tc.problem_id
    await db.delete(tc)
    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="DELETE_TEST_CASE",
        resource_type="test_case",
        resource_id=str(test_case_id),
        details={"problem_id": str(prob_id)},
    )
    await db.commit()

    return {"message": "Test case deleted successfully"}


# 6. Hint Management
@router.post("/problems/{problem_id}/hints", status_code=status.HTTP_201_CREATED)
async def create_hint_admin(
    problem_id: uuid.UUID,
    body: AdminHintCreateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Creates a progressive static hint for a problem."""
    hint = Hint(
        id=uuid.uuid4(),
        problem_id=problem_id,
        step_number=body.step_number,
        title=body.title,
        content_markdown=body.content_markdown,
    )
    db.add(hint)
    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="CREATE_HINT",
        resource_type="hint",
        resource_id=str(hint.id),
        details={"problem_id": str(problem_id), "step_number": hint.step_number},
    )
    await db.commit()

    return {"id": str(hint.id), "step_number": hint.step_number}


@router.delete("/hints/{hint_id}")
async def delete_hint_admin(
    hint_id: uuid.UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a static hint."""
    hint = (await db.execute(select(Hint).where(Hint.id == hint_id))).scalar_one_or_none()
    if not hint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hint not found.")

    prob_id = hint.problem_id
    await db.delete(hint)
    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="DELETE_HINT",
        resource_type="hint",
        resource_id=str(hint_id),
        details={"problem_id": str(prob_id)},
    )
    await db.commit()

    return {"message": "Hint deleted successfully"}


# 7. Mock Test Management
@router.get("/mock-tests")
async def list_mock_tests_admin(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Lists all mock test templates."""
    stmt = (
        select(MockTest)
        .options(
            selectinload(MockTest.company),
            selectinload(MockTest.test_problems).selectinload(MockTestProblem.problem),
        )
        .order_by(MockTest.created_at.desc())
    )
    mocks = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": str(m.id),
            "company_name": m.company.name if m.company else "Unknown",
            "title": m.title,
            "description": m.description,
            "duration_minutes": m.duration_minutes,
            "problem_count": len(m.test_problems),
            "total_points": sum(tp.weight_score for tp in m.test_problems),
        }
        for m in mocks
    ]


@router.post("/mock-tests", status_code=status.HTTP_201_CREATED)
async def create_mock_test_admin(
    body: AdminMockTestCreateRequest,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new mock test template and assigns problem weight scores."""
    mock_id = uuid.uuid4()
    mock = MockTest(
        id=mock_id,
        company_id=body.company_id,
        title=body.title,
        description=body.description,
        duration_minutes=body.duration_minutes,
    )
    db.add(mock)
    await db.flush()

    for assignment in body.problem_assignments:
        db.add(MockTestProblem(
            id=uuid.uuid4(),
            mock_test_id=mock_id,
            problem_id=assignment.problem_id,
            order_index=assignment.order_index,
            weight_score=assignment.weight_score,
        ))

    await db.commit()

    await record_audit_log(
        db=db,
        user_id=admin_user.id,
        action="CREATE_MOCK_TEST",
        resource_type="mock_test",
        resource_id=str(mock_id),
        details={"title": mock.title, "duration_minutes": mock.duration_minutes},
    )
    await db.commit()

    return {"id": str(mock_id), "title": mock.title}


# 8. Audit Log Inspector
@router.get("/audit-logs", response_model=AuditLogPaginatedResponse)
async def get_audit_logs_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves paginated administrator audit logs."""
    base_stmt = select(AuditLog).options(selectinload(AuditLog.user))

    filters = []
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if action:
        filters.append(AuditLog.action == action)

    if filters:
        base_stmt = base_stmt.where(and_(*filters))

    count_stmt = select(func.count(AuditLog.id))
    if filters:
        count_stmt = count_stmt.where(and_(*filters))

    total = (await db.execute(count_stmt)).scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    query = base_stmt.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    logs = (await db.execute(query)).scalars().all()

    items = [
        AuditLogItem(
            id=log.id,
            user_id=log.user_id,
            user_email=log.user.email if log.user else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            timestamp=log.timestamp,
        )
        for log in logs
    ]

    return AuditLogPaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

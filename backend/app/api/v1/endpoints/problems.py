import math
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_current_user
from app.models.user import User
from app.models.company import Company
from app.models.problem import Problem, Topic, ProblemTopic, ProblemCompany, TestCase, Hint, DifficultyLevel
from app.models.submission import UserProblemProgress, ProgressStatus
from app.schemas.problem import (
    ProblemListItemOut, ProblemDetailOut, ProblemPaginatedResponse,
    TopicOut, HintOut, BookmarkRequest, NotesRequest, TestCaseOut
)

router = APIRouter()


@router.get("/topics", response_model=List[TopicOut])
async def list_topics(db: AsyncSession = Depends(get_db)):
    """Retrieve all available DSA topics."""
    stmt = select(Topic).order_by(Topic.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("", response_model=ProblemPaginatedResponse)
async def list_problems(
    company: Optional[str] = Query(None, description="Company slug filter"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Difficulty level filter"),
    topic: Optional[str] = Query(None, description="Topic slug filter"),
    status: Optional[ProgressStatus] = Query(None, description="User status filter"),
    search: Optional[str] = Query(None, description="Problem title search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve paginated problem catalog with search and filters."""
    query = select(Problem).where(Problem.is_active == True).options(
        selectinload(Problem.topic_associations).selectinload(ProblemTopic.topic),
        selectinload(Problem.company_associations).selectinload(ProblemCompany.company)
    )

    # Search filter
    if search:
        query = query.where(Problem.title.ilike(f"%{search}%"))

    # Difficulty filter
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)

    # Topic filter
    if topic:
        query = query.join(ProblemTopic).join(Topic).where(Topic.slug == topic)

    # Company filter
    if company:
        query = query.join(ProblemCompany).join(Company).where(Company.slug == company)

    # Distinct problem IDs for counting
    count_query = select(func.count(func.distinct(Problem.id))).where(Problem.is_active == True)

    if search:
        count_query = count_query.where(Problem.title.ilike(f"%{search}%"))
    if difficulty:
        count_query = count_query.where(Problem.difficulty == difficulty)
    if topic:
        count_query = count_query.join(ProblemTopic).join(Topic).where(Topic.slug == topic)
    if company:
        count_query = count_query.join(ProblemCompany).join(Company).where(Company.slug == company)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Apply pagination
    query = query.order_by(Problem.title).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    problems = result.scalars().unique().all()

    # Load user progress if authenticated
    user_progress_map = {}
    if current_user:
        prob_ids = [p.id for p in problems]
        if prob_ids:
            prog_stmt = select(UserProblemProgress).where(
                and_(
                    UserProblemProgress.user_id == current_user.id,
                    UserProblemProgress.problem_id.in_(prob_ids)
                )
            )
            prog_result = await db.execute(prog_stmt)
            for prog in prog_result.scalars().all():
                user_progress_map[prog.problem_id] = prog

    items = []
    for p in problems:
        prog = user_progress_map.get(p.id)
        user_status = prog.status if prog else ProgressStatus.UNATTEMPTED
        is_bookmarked = prog.is_bookmarked if prog else False

        # Apply status filter if provided
        if status and user_status != status:
            continue

        items.append(
            ProblemListItemOut(
                id=p.id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty,
                category=p.category,
                topics=p.topics,
                companies=p.companies,
                user_status=user_status,
                is_bookmarked=is_bookmarked
            )
        )

    return ProblemPaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )


@router.get("/{slug}", response_model=ProblemDetailOut)
async def get_problem_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve problem details for authenticated user. Hidden test cases and reference solution are excluded."""
    stmt = (
        select(Problem)
        .where(and_(Problem.slug == slug, Problem.is_active == True))

        .options(
            selectinload(Problem.topic_associations).selectinload(ProblemTopic.topic),
            selectinload(Problem.company_associations).selectinload(ProblemCompany.company),
            selectinload(Problem.test_cases),
            selectinload(Problem.hints)
        )
    )
    result = await db.execute(stmt)
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # Load user progress
    prog_stmt = select(UserProblemProgress).where(
        and_(
            UserProblemProgress.user_id == current_user.id,
            UserProblemProgress.problem_id == problem.id
        )
    )
    prog_result = await db.execute(prog_stmt)
    user_prog = prog_result.scalar_one_or_none()

    user_status = user_prog.status if user_prog else ProgressStatus.UNATTEMPTED
    hints_unlocked_count = user_prog.hints_unlocked if user_prog else 0
    is_bookmarked = user_prog.is_bookmarked if user_prog else False
    personal_notes = user_prog.personal_notes if user_prog else None

    # Filter sample test cases ONLY (is_sample == True)
    sample_cases = [tc for tc in problem.test_cases if tc.is_sample]

    # Filter unlocked hints ONLY (step_number <= hints_unlocked_count)
    unlocked_hints = sorted(
        [h for h in problem.hints if h.step_number <= hints_unlocked_count],
        key=lambda x: x.step_number
    )

    return ProblemDetailOut(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        description_markdown=problem.description_markdown,
        difficulty=problem.difficulty,
        category=problem.category,
        constraints_text=problem.constraints_text,
        starter_code=problem.starter_code,
        topics=problem.topics,
        companies=problem.companies,
        sample_test_cases=sample_cases,
        user_status=user_status,
        hints_unlocked=hints_unlocked_count,
        hints=unlocked_hints,
        is_bookmarked=is_bookmarked,
        personal_notes=personal_notes
    )


@router.post("/{problem_id}/hints/unlock", response_model=HintOut)
async def unlock_next_hint(
    problem_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Progressively unlock the next hint (up to 3 max)."""
    # Fetch problem hints
    hints_stmt = select(Hint).where(Hint.problem_id == problem_id).order_by(Hint.step_number)
    result = await db.execute(hints_stmt)
    all_hints = result.scalars().all()

    if not all_hints:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hints available for this problem")

    # Fetch or create progress record
    prog_stmt = select(UserProblemProgress).where(
        and_(
            UserProblemProgress.user_id == current_user.id,
            UserProblemProgress.problem_id == problem_id
        )
    )
    prog_res = await db.execute(prog_stmt)
    user_prog = prog_res.scalar_one_or_none()

    if not user_prog:
        user_prog = UserProblemProgress(
            user_id=current_user.id,
            problem_id=problem_id,
            status=ProgressStatus.UNATTEMPTED,
            hints_unlocked=0
        )
        db.add(user_prog)
        await db.flush()

    if user_prog.hints_unlocked >= len(all_hints) or user_prog.hints_unlocked >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All available hints for this problem have already been unlocked."
        )

    # Increment hint count
    user_prog.hints_unlocked += 1
    await db.commit()

    unlocked_hint = next(h for h in all_hints if h.step_number == user_prog.hints_unlocked)
    return unlocked_hint


@router.patch("/{problem_id}/bookmark")
async def toggle_bookmark(
    problem_id: uuid.UUID,
    body: BookmarkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle bookmark status for a problem."""
    prog_stmt = select(UserProblemProgress).where(
        and_(
            UserProblemProgress.user_id == current_user.id,
            UserProblemProgress.problem_id == problem_id
        )
    )
    prog_res = await db.execute(prog_stmt)
    user_prog = prog_res.scalar_one_or_none()

    if not user_prog:
        user_prog = UserProblemProgress(
            user_id=current_user.id,
            problem_id=problem_id,
            status=ProgressStatus.UNATTEMPTED,
            is_bookmarked=body.is_bookmarked
        )
        db.add(user_prog)
    else:
        user_prog.is_bookmarked = body.is_bookmarked

    await db.commit()
    return {"message": "Bookmark updated successfully", "is_bookmarked": body.is_bookmarked}


@router.patch("/{problem_id}/notes")
async def update_notes(
    problem_id: uuid.UUID,
    body: NotesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save or update personal notes for a problem."""
    prog_stmt = select(UserProblemProgress).where(
        and_(
            UserProblemProgress.user_id == current_user.id,
            UserProblemProgress.problem_id == problem_id
        )
    )
    prog_res = await db.execute(prog_stmt)
    user_prog = prog_res.scalar_one_or_none()

    if not user_prog:
        user_prog = UserProblemProgress(
            user_id=current_user.id,
            problem_id=problem_id,
            status=ProgressStatus.UNATTEMPTED,
            personal_notes=body.personal_notes
        )
        db.add(user_prog)
    else:
        user_prog.personal_notes = body.personal_notes

    await db.commit()
    return {"message": "Personal notes updated successfully", "personal_notes": body.personal_notes}

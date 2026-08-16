import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

from app.models.user import User
from app.models.company import Company
from app.models.problem import Problem, DifficultyLevel, ProblemTopic
from app.models.submission import Submission, UserProblemProgress, ProgressStatus, SubmissionStatus
from app.models.mock_test import MockTest, MockTestProblem, UserMockTest, UserMockTestSubmission, MockTestStatus
from app.schemas.mock_test import (
    MockTestCatalogItem,
    UserMockTestSessionResponse,
    MockTestProblemItem,
    SubmitMockProblemResponse,
    MockTestResultResponse,
    MockTestResultProblemDetail,
    MockTestTopicPerformance,
    MockTestDifficultyPerformance,
    MockTestHistoryItem,
)
from app.services.execution import ExecutionService
from app.services.recommendation import RecommendationEngine
from app.services.ai.base import AIService
from app.services.gamification import GamificationService


logger = logging.getLogger(__name__)


def make_aware(dt: datetime) -> datetime:
    """Ensures datetime instance is timezone-aware UTC."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class MockTestService:
    """Server-authoritative mock test lifecycle, timed scoring, and evaluation service."""

    def __init__(self, db: AsyncSession, ai_service: Optional[AIService] = None):
        self.db = db
        self.ai_service = ai_service

    async def get_catalog(self, user: User) -> List[MockTestCatalogItem]:
        """Returns mock test catalog relevant to candidate's selected target companies."""
        target_company_ids = [tc.company_id for tc in user.target_companies] if user.target_companies else []
        if not target_company_ids:
            return []

        stmt = (
            select(MockTest)
            .where(MockTest.company_id.in_(target_company_ids))
            .options(
                selectinload(MockTest.company),
                selectinload(MockTest.test_problems),
            )
        )
        res = await self.db.execute(stmt)
        mocks = res.scalars().all()

        # Fetch candidate's previous attempts for these mocks
        attempt_stmt = select(UserMockTest).where(
            UserMockTest.user_id == user.id,
            UserMockTest.mock_test_id.in_([m.id for m in mocks])
        ).order_by(UserMockTest.started_at.desc())
        attempt_res = await self.db.execute(attempt_stmt)
        user_attempts = attempt_res.scalars().all()

        attempt_map: Dict[uuid.UUID, UserMockTest] = {}
        for att in user_attempts:
            if att.mock_test_id not in attempt_map:
                attempt_map[att.mock_test_id] = att

        catalog_items = []
        for m in mocks:
            last_att = attempt_map.get(m.id)
            tot_pts = sum(p.weight_score for p in m.test_problems)
            catalog_items.append(
                MockTestCatalogItem(
                    id=m.id,
                    company_id=m.company_id,
                    company_name=m.company.name,
                    company_slug=m.company.slug,
                    title=m.title,
                    description=m.description,
                    duration_minutes=m.duration_minutes,
                    problem_count=len(m.test_problems),
                    total_points=tot_pts,
                    user_last_status=last_att.status.value if last_att else None,
                    user_last_score=last_att.total_score if last_att else None,
                )
            )

        return catalog_items

    async def start_mock_test(self, user: User, mock_test_id: uuid.UUID) -> UserMockTestSessionResponse:
        """Starts a new mock test session or resumes an active in-progress session."""
        stmt = (
            select(MockTest)
            .where(MockTest.id == mock_test_id)
            .options(
                selectinload(MockTest.company),
                selectinload(MockTest.test_problems).selectinload(MockTestProblem.problem),
            )
        )
        res = await self.db.execute(stmt)
        mock = res.scalar_one_or_none()

        if not mock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock test template not found.")

        target_company_ids = [tc.company_id for tc in user.target_companies] if user.target_companies else []
        if mock.company_id not in target_company_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This mock test belongs to a company not in your target companies list.",
            )

        active_stmt = (
            select(UserMockTest)
            .where(
                UserMockTest.user_id == user.id,
                UserMockTest.mock_test_id == mock_test_id,
                UserMockTest.status == MockTestStatus.IN_PROGRESS,
            )
            .options(
                selectinload(UserMockTest.mock_test).selectinload(MockTest.company),
                selectinload(UserMockTest.mock_test).selectinload(MockTest.test_problems).selectinload(MockTestProblem.problem),
                selectinload(UserMockTest.submissions),
            )
        )
        active_res = await self.db.execute(active_stmt)
        active_session = active_res.scalar_one_or_none()

        now_utc = datetime.now(timezone.utc)

        if active_session:
            started_at = make_aware(active_session.started_at)
            expires_at = started_at + timedelta(minutes=mock.duration_minutes)
            rem_secs = max(0, int((expires_at - now_utc).total_seconds()))
            if rem_secs > 0:
                return await self._format_session_response(active_session, mock, rem_secs)
            else:
                await self._finalize_auto_submit(active_session, mock)

        max_score = sum(p.weight_score for p in mock.test_problems)
        new_session = UserMockTest(
            id=uuid.uuid4(),
            user_id=user.id,
            mock_test_id=mock_test_id,
            status=MockTestStatus.IN_PROGRESS,
            total_score=0,
            max_possible_score=max_score,
            started_at=now_utc,
        )
        self.db.add(new_session)
        await self.db.commit()

        res_new = await self.db.execute(
            select(UserMockTest)
            .where(UserMockTest.id == new_session.id)
            .options(
                selectinload(UserMockTest.mock_test).selectinload(MockTest.company),
                selectinload(UserMockTest.mock_test).selectinload(MockTest.test_problems).selectinload(MockTestProblem.problem),
                selectinload(UserMockTest.submissions),
            )
        )
        session_obj = res_new.scalar_one()

        started_at = make_aware(session_obj.started_at)
        expires_at = started_at + timedelta(minutes=mock.duration_minutes)
        rem_secs = max(0, int((expires_at - now_utc).total_seconds()))

        return await self._format_session_response(session_obj, mock, rem_secs)

    async def get_session(self, user: User, session_id: uuid.UUID) -> UserMockTestSessionResponse:
        """Retrieves active session details and recalculates remaining time server-side."""
        stmt = (
            select(UserMockTest)
            .where(UserMockTest.id == session_id)
            .options(
                selectinload(UserMockTest.mock_test).selectinload(MockTest.company),
                selectinload(UserMockTest.mock_test).selectinload(MockTest.test_problems).selectinload(MockTestProblem.problem),
                selectinload(UserMockTest.submissions),
            )
        )
        res = await self.db.execute(stmt)
        session_obj = res.scalar_one_or_none()

        if not session_obj or session_obj.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock test session not found.")

        mock = session_obj.mock_test
        now_utc = datetime.now(timezone.utc)
        started_at = make_aware(session_obj.started_at)
        expires_at = started_at + timedelta(minutes=mock.duration_minutes)
        rem_secs = max(0, int((expires_at - now_utc).total_seconds()))

        if rem_secs == 0 and session_obj.status == MockTestStatus.IN_PROGRESS:
            await self._finalize_auto_submit(session_obj, mock)

        return await self._format_session_response(session_obj, mock, rem_secs)

    async def submit_problem_solution(
        self,
        user: User,
        session_id: uuid.UUID,
        problem_id: uuid.UUID,
        language: str,
        code: str,
        execution_service: ExecutionService,
    ) -> SubmitMockProblemResponse:
        """Executes candidate code against hidden evaluation test cases during a mock test."""
        stmt = (
            select(UserMockTest)
            .where(UserMockTest.id == session_id)
            .options(
                selectinload(UserMockTest.mock_test).selectinload(MockTest.test_problems),
                selectinload(UserMockTest.submissions),
            )
        )
        res = await self.db.execute(stmt)
        session_obj = res.scalar_one_or_none()

        if not session_obj or session_obj.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock test session not found.")

        now_utc = datetime.now(timezone.utc)
        started_at = make_aware(session_obj.started_at)
        expires_at = started_at + timedelta(minutes=session_obj.mock_test.duration_minutes)
        if now_utc >= expires_at or session_obj.status != MockTestStatus.IN_PROGRESS:
            if session_obj.status == MockTestStatus.IN_PROGRESS:
                await self._finalize_auto_submit(session_obj, session_obj.mock_test)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This mock test session has expired or is already completed.",
            )

        test_prob = next((tp for tp in session_obj.mock_test.test_problems if tp.problem_id == problem_id), None)
        if not test_prob:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Problem is not part of this mock test.")

        prob_stmt = select(Problem).where(Problem.id == problem_id).options(selectinload(Problem.test_cases))
        prob_res = await self.db.execute(prob_stmt)
        problem_obj = prob_res.scalar_one_or_none()

        if not problem_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")

        formatted_test_cases = [
            {"input_data": tc.input_data, "expected_output": tc.expected_output}
            for tc in problem_obj.test_cases
        ]

        exec_res = await execution_service.execute_submission(
            language=language,
            source_code=code,
            test_cases=formatted_test_cases,
        )

        pts_weight = test_prob.weight_score
        if exec_res.overall_status == SubmissionStatus.ACCEPTED:
            pts_obtained = pts_weight
        elif exec_res.total_test_cases > 0:
            pts_obtained = int(round((exec_res.passed_test_cases / exec_res.total_test_cases) * pts_weight))
        else:
            pts_obtained = 0

        base_sub = Submission(
            user_id=user.id,
            problem_id=problem_id,
            language=language,
            code=code,
            status=exec_res.overall_status,
            execution_time_ms=exec_res.execution_time_ms,
            memory_kb=exec_res.memory_kb,
            passed_test_cases=exec_res.passed_test_cases,
            total_test_cases=exec_res.total_test_cases,
            error_output=exec_res.error_output,
        )
        self.db.add(base_sub)
        await self.db.flush()

        sub_stmt = select(UserMockTestSubmission).where(
            UserMockTestSubmission.user_mock_test_id == session_id,
            UserMockTestSubmission.problem_id == problem_id,
        )
        sub_res = await self.db.execute(sub_stmt)
        mock_sub = sub_res.scalar_one_or_none()

        if not mock_sub:
            mock_sub = UserMockTestSubmission(
                id=uuid.uuid4(),
                user_mock_test_id=session_id,
                problem_id=problem_id,
                submission_id=base_sub.id,
                score_obtained=pts_obtained,
            )
            self.db.add(mock_sub)
        else:
            if pts_obtained > mock_sub.score_obtained:
                mock_sub.score_obtained = pts_obtained
                mock_sub.submission_id = base_sub.id

        prog_stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.problem_id == problem_id,
        )
        prog_res = await self.db.execute(prog_stmt)
        user_prog = prog_res.scalar_one_or_none()

        if not user_prog:
            user_prog = UserProblemProgress(
                user_id=user.id,
                problem_id=problem_id,
                status=ProgressStatus.SOLVED if exec_res.overall_status == SubmissionStatus.ACCEPTED else ProgressStatus.ATTEMPTED,
                attempts_count=1,
            )
            self.db.add(user_prog)
        else:
            user_prog.attempts_count += 1
            if exec_res.overall_status == SubmissionStatus.ACCEPTED:
                user_prog.status = ProgressStatus.SOLVED

        await self.db.commit()

        return SubmitMockProblemResponse(
            submission_id=base_sub.id,
            status=exec_res.overall_status,
            passed_test_cases=exec_res.passed_test_cases,
            total_test_cases=exec_res.total_test_cases,
            score_obtained=pts_obtained,
            execution_time_ms=exec_res.execution_time_ms,
            memory_kb=exec_res.memory_kb,
            error_output=exec_res.error_output,
        )

    async def submit_mock_test(self, user: User, session_id: uuid.UUID) -> MockTestResultResponse:
        """Finalizes and scores an active mock test session."""
        stmt = (
            select(UserMockTest)
            .where(UserMockTest.id == session_id)
            .options(
                selectinload(UserMockTest.mock_test).selectinload(MockTest.company),
                selectinload(UserMockTest.mock_test).selectinload(MockTest.test_problems).selectinload(MockTestProblem.problem),
                selectinload(UserMockTest.submissions).selectinload(UserMockTestSubmission.submission),
            )
        )
        res = await self.db.execute(stmt)
        session_obj = res.scalar_one_or_none()

        if not session_obj or session_obj.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock test session not found.")

        now_utc = datetime.now(timezone.utc)

        if session_obj.status == MockTestStatus.IN_PROGRESS:
            tot_score = sum(s.score_obtained for s in session_obj.submissions)
            session_obj.total_score = tot_score
            session_obj.status = MockTestStatus.SUBMITTED
            session_obj.completed_at = now_utc
            await self.db.commit()

            try:
                await GamificationService.process_mock_completion(
                    db=self.db, user_id=user.id, session=session_obj, mock=session_obj.mock_test
                )
                await self.db.commit()
            except Exception as e:
                logger.error(f"Failed to process gamification mock completion: {e}")


        return await self.get_mock_test_result(user, session_id)

    async def get_mock_test_result(self, user: User, session_id: uuid.UUID) -> MockTestResultResponse:
        """Calculates detailed score breakdown, topic/difficulty analysis, and post-test next steps."""
        stmt = (
            select(UserMockTest)
            .where(UserMockTest.id == session_id)
            .options(
                selectinload(UserMockTest.mock_test).selectinload(MockTest.company),
                selectinload(UserMockTest.mock_test).selectinload(MockTest.test_problems).selectinload(MockTestProblem.problem).selectinload(Problem.topic_associations).selectinload(ProblemTopic.topic),
                selectinload(UserMockTest.submissions).selectinload(UserMockTestSubmission.submission),
            )
        )
        res = await self.db.execute(stmt)
        session_obj = res.scalar_one_or_none()

        if not session_obj or session_obj.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock test session not found.")

        mock = session_obj.mock_test
        tot_pts = session_obj.max_possible_score or sum(p.weight_score for p in mock.test_problems)
        score = session_obj.total_score
        pct = round((score / max(tot_pts, 1)) * 100, 1)

        started_at = make_aware(session_obj.started_at)
        completed_time = make_aware(session_obj.completed_at) if session_obj.completed_at else datetime.now(timezone.utc)
        time_taken = int((completed_time - started_at).total_seconds())

        submission_map = {s.problem_id: s for s in session_obj.submissions}

        prob_details: List[MockTestResultProblemDetail] = []
        topic_counts: Dict[uuid.UUID, Dict[str, Any]] = {}
        diff_counts: Dict[str, Dict[str, int]] = {
            "EASY": {"problems": 0, "solved": 0},
            "MEDIUM": {"problems": 0, "solved": 0},
            "HARD": {"problems": 0, "solved": 0},
        }

        for tp in mock.test_problems:
            p = tp.problem
            sub = submission_map.get(p.id)
            p_status = sub.submission.status if sub and sub.submission else "UNATTEMPTED"
            is_solved = p_status == "ACCEPTED" or (sub and sub.score_obtained == tp.weight_score)

            prob_details.append(
                MockTestResultProblemDetail(
                    problem_id=p.id,
                    title=p.title,
                    slug=p.slug,
                    difficulty=p.difficulty.value,
                    order_index=tp.order_index,
                    weight_score=tp.weight_score,
                    score_obtained=sub.score_obtained if sub else 0,
                    status=p_status,
                    passed_test_cases=sub.submission.passed_test_cases if sub and sub.submission else 0,
                    total_test_cases=sub.submission.total_test_cases if sub and sub.submission else 0,
                )
            )

            d_val = p.difficulty.value
            diff_counts[d_val]["problems"] += 1
            if is_solved:
                diff_counts[d_val]["solved"] += 1

            for pt in p.topic_associations:
                t = pt.topic
                if t.id not in topic_counts:
                    topic_counts[t.id] = {"id": t.id, "name": t.name, "problems": 0, "solved": 0}
                topic_counts[t.id]["problems"] += 1
                if is_solved:
                    topic_counts[t.id]["solved"] += 1

        topic_breakdown = [
            MockTestTopicPerformance(
                topic_id=info["id"],
                topic_name=info["name"],
                problems_count=info["problems"],
                solved_count=info["solved"],
                status="STRONG" if info["solved"] == info["problems"] else "NEEDS_PRACTICE",
            )
            for info in topic_counts.values()
        ]

        difficulty_breakdown = [
            MockTestDifficultyPerformance(
                difficulty=d_name,
                problems_count=info["problems"],
                solved_count=info["solved"],
            )
            for d_name, info in diff_counts.items()
            if info["problems"] > 0
        ]

        weak_topics = [tb.topic_name for tb in topic_breakdown if tb.status == "NEEDS_PRACTICE"]
        next_steps = []
        if weak_topics:
            next_steps.append(f"Practice {weak_topics[0]} problems to strengthen your target accuracy.")
        if diff_counts["MEDIUM"]["problems"] > 0 and diff_counts["MEDIUM"]["solved"] < diff_counts["MEDIUM"]["problems"]:
            next_steps.append("Focus on Medium-difficulty problem-solving speed.")
        if not next_steps:
            next_steps.append("Great performance! Take a Full Mock Assessment next.")

        ai_exp = None
        if self.ai_service:
            try:
                ai_exp = f"You achieved {score}/{tot_pts} ({pct}%) on the {mock.title}. Focus next on {weak_topics[0] if weak_topics else 'maintaining your accuracy'}."
            except Exception as e:
                logger.warning(f"AI post-mock summary fallback: {e}")

        return MockTestResultResponse(
            session_id=session_obj.id,
            mock_test_id=mock.id,
            title=mock.title,
            company_name=mock.company.name,
            status=session_obj.status.value,
            score=score,
            total_points=tot_pts,
            percentage=pct,
            time_taken_seconds=time_taken,
            started_at=started_at,
            completed_at=completed_time,
            problems=prob_details,
            topic_breakdown=topic_breakdown,
            difficulty_breakdown=difficulty_breakdown,
            recommended_next_steps=next_steps,
            ai_explanation=ai_exp,
        )

    async def get_user_history(self, user: User) -> List[MockTestHistoryItem]:
        """Retrieves list of completed mock tests taken by candidate."""
        stmt = (
            select(UserMockTest)
            .where(
                UserMockTest.user_id == user.id,
                UserMockTest.status.in_([MockTestStatus.SUBMITTED, MockTestStatus.AUTO_SUBMITTED, MockTestStatus.COMPLETED, MockTestStatus.TIMED_OUT])
            )
            .options(selectinload(UserMockTest.mock_test).selectinload(MockTest.company))
            .order_by(UserMockTest.completed_at.desc())
        )
        res = await self.db.execute(stmt)
        attempts = res.scalars().all()

        history = []
        for att in attempts:
            tot = att.max_possible_score or 100
            pct = round((att.total_score / max(tot, 1)) * 100, 1)
            history.append(
                MockTestHistoryItem(
                    session_id=att.id,
                    mock_test_id=att.mock_test_id,
                    title=att.mock_test.title,
                    company_name=att.mock_test.company.name,
                    company_slug=att.mock_test.company.slug,
                    status=att.status.value,
                    score=att.total_score,
                    total_points=tot,
                    percentage=pct,
                    completed_at=att.completed_at,
                )
            )

        return history

    async def _finalize_auto_submit(self, session_obj: UserMockTest, mock: MockTest):
        """Automatically submits expired session server-side."""
        tot_score = sum(s.score_obtained for s in session_obj.submissions)
        session_obj.total_score = tot_score
        session_obj.status = MockTestStatus.AUTO_SUBMITTED
        started_at = make_aware(session_obj.started_at)
        session_obj.completed_at = started_at + timedelta(minutes=mock.duration_minutes)
        await self.db.commit()

        try:
            await GamificationService.process_mock_completion(
                db=self.db, user_id=session_obj.user_id, session=session_obj, mock=mock
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to process gamification auto submit: {e}")


    async def _format_session_response(
        self,
        session_obj: UserMockTest,
        mock: MockTest,
        remaining_seconds: int,
    ) -> UserMockTestSessionResponse:

        submission_map = {s.problem_id: s for s in session_obj.submissions}

        prob_items = []
        for tp in mock.test_problems:
            p = tp.problem
            sub = submission_map.get(p.id)
            u_status = "UNATTEMPTED"
            if sub:
                u_status = "SOLVED" if sub.score_obtained == tp.weight_score else "ATTEMPTED"

            prob_items.append(
                MockTestProblemItem(
                    problem_id=p.id,
                    title=p.title,
                    slug=p.slug,
                    difficulty=p.difficulty.value,
                    category=p.category,
                    order_index=tp.order_index,
                    weight_score=tp.weight_score,
                    user_status=u_status,
                    score_obtained=sub.score_obtained if sub else 0,
                    code_draft=sub.submission.code if sub and sub.submission else None,
                )
            )

        started_at = make_aware(session_obj.started_at)
        return UserMockTestSessionResponse(
            session_id=session_obj.id,
            mock_test_id=mock.id,
            title=mock.title,
            company_name=mock.company.name,
            company_slug=mock.company.slug,
            duration_minutes=mock.duration_minutes,
            started_at=started_at,
            expires_at=started_at + timedelta(minutes=mock.duration_minutes),
            remaining_seconds=remaining_seconds,
            status=session_obj.status.value,
            total_score=session_obj.total_score,
            max_possible_score=session_obj.max_possible_score,
            problems=prob_items,
        )

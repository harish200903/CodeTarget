import logging
import uuid
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user import User, SkillLevel
from app.models.company import Company
from app.models.problem import Problem, Topic, ProblemCompany, ProblemTopic, DifficultyLevel
from app.models.submission import Submission, UserProblemProgress, ProgressStatus
from app.schemas.company_prep import (
    CompanyInfo,
    TopicBreakdownItem,
    DifficultyBreakdownItem,
    CoverageMetrics,
    ProblemCounts,
    CompanyPreparationResponse,
)
from app.services.ai.base import AIService

logger = logging.getLogger(__name__)


class CompanyPreparationEngine:
    """Calculates authoritative, deterministic company preparation metrics and explanations."""

    def __init__(self, db: AsyncSession, ai_service: Optional[AIService] = None):
        self.db = db
        self.ai_service = ai_service

    async def get_company_preparation(
        self,
        user: User,
        company_id: uuid.UUID,
    ) -> CompanyPreparationResponse:
        """Calculates preparation metrics for a specific target company."""
        # 1. Authorize Target Company Access
        target_company_ids = [tc.company_id for tc in user.target_companies] if user.target_companies else []
        if company_id not in target_company_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company is not in your selected target companies list. Please complete onboarding or update your profile.",
            )

        # 2. Fetch Company metadata
        comp_stmt = select(Company).where(Company.id == company_id)
        comp_res = await self.db.execute(comp_stmt)
        company = comp_res.scalar_one_or_none()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target company not found.",
            )

        company_info = CompanyInfo(id=company.id, name=company.name, slug=company.slug)

        # 3. Query Company Problem Pool
        probs_stmt = (
            select(Problem)
            .join(ProblemCompany, ProblemCompany.problem_id == Problem.id)
            .where(ProblemCompany.company_id == company_id)
            .options(
                selectinload(Problem.topic_associations).selectinload(ProblemTopic.topic),
            )
            .distinct()
        )
        probs_res = await self.db.execute(probs_stmt)
        company_problems = probs_res.scalars().all()
        total_available = len(company_problems)

        if total_available == 0:
            return CompanyPreparationResponse(
                company=company_info,
                preparation_score=None,
                status="INSUFFICIENT_DATA",
                confidence_message="No practice problems currently seeded for this company.",
                coverage=CoverageMetrics(overall=0.0, topics=0.0, difficulty=0.0),
                problems=ProblemCounts(available=0, attempted=0, solved=0),
                topic_breakdown=[],
                difficulty_breakdown=[],
                strengths=["No data available yet"],
                focus_areas=["Solve curated problems"],
                recommended_next_steps=["Explore general DSA catalog"],
                ai_explanation=None,
            )

        company_problem_ids = [p.id for p in company_problems]

        # 4. Fetch Candidate Progress on Company Problems
        prog_stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.problem_id.in_(company_problem_ids),
        )
        prog_res = await self.db.execute(prog_stmt)
        user_progress_list = prog_res.scalars().all()

        progress_map = {p.problem_id: p for p in user_progress_list}
        attempted_ids = {p.problem_id for p in user_progress_list if p.status in (ProgressStatus.ATTEMPTED, ProgressStatus.SOLVED)}
        solved_ids = {p.problem_id for p in user_progress_list if p.status == ProgressStatus.SOLVED}

        attempted_count = len(attempted_ids)
        solved_count = len(solved_ids)

        # 5. Cold Start & Insufficient Data State Check
        if attempted_count < 2:
            unsolved_next = [p.title for p in company_problems if p.id not in solved_ids][:3]
            return CompanyPreparationResponse(
                company=company_info,
                preparation_score=None,
                status="INSUFFICIENT_DATA",
                confidence_message="Complete a few company-relevant problems to establish your CodeTarget preparation baseline.",
                coverage=CoverageMetrics(
                    overall=round((solved_count / max(total_available, 1)) * 100, 1),
                    topics=0.0,
                    difficulty=0.0,
                ),
                problems=ProblemCounts(
                    available=total_available,
                    attempted=attempted_count,
                    solved=solved_count,
                ),
                topic_breakdown=[],
                difficulty_breakdown=[],
                strengths=["Onboarding profile established"],
                focus_areas=["Solve your first 2 company-relevant problems"],
                recommended_next_steps=[f"Solve {title}" for title in unsolved_next],
                ai_explanation="Your preparation score will generate after completing at least 2 practice problems.",
            )

        # 6. Topic Breakdown Calculation
        topic_map: Dict[uuid.UUID, Dict[str, Any]] = {}
        for prob in company_problems:
            is_att = prob.id in attempted_ids
            is_sol = prob.id in solved_ids
            for pt in prob.topic_associations:
                t = pt.topic
                if t.id not in topic_map:
                    topic_map[t.id] = {
                        "id": t.id,
                        "name": t.name,
                        "available": 0,
                        "attempted": 0,
                        "solved": 0,
                    }
                topic_map[t.id]["available"] += 1
                if is_att:
                    topic_map[t.id]["attempted"] += 1
                if is_sol:
                    topic_map[t.id]["solved"] += 1

        topic_breakdown: List[TopicBreakdownItem] = []
        covered_topics_count = 0

        for t_info in topic_map.values():
            att = t_info["attempted"]
            sol = t_info["solved"]
            avail = t_info["available"]

            solve_rate = round((sol / max(att, 1)) * 100, 1)
            coverage_pct = round((att / max(avail, 1)) * 100, 1)

            if sol > 0:
                covered_topics_count += 1

            if att == 0:
                t_status = "NOT_STARTED"
            elif solve_rate < 50.0:
                t_status = "NEEDS_PRACTICE"
            elif solve_rate < 80.0:
                t_status = "DEVELOPING"
            else:
                t_status = "STRONG"

            topic_breakdown.append(
                TopicBreakdownItem(
                    topic_id=t_info["id"],
                    topic_name=t_info["name"],
                    available=avail,
                    attempted=att,
                    solved=sol,
                    solve_rate=solve_rate,
                    coverage_pct=coverage_pct,
                    status=t_status,
                )
            )

        topic_breakdown.sort(key=lambda x: x.coverage_pct, reverse=True)

        # 7. Difficulty Breakdown Calculation
        diff_stats = {
            DifficultyLevel.EASY: {"available": 0, "attempted": 0, "solved": 0},
            DifficultyLevel.MEDIUM: {"available": 0, "attempted": 0, "solved": 0},
            DifficultyLevel.HARD: {"available": 0, "attempted": 0, "solved": 0},
        }

        for prob in company_problems:
            d = prob.difficulty
            diff_stats[d]["available"] += 1
            if prob.id in attempted_ids:
                diff_stats[d]["attempted"] += 1
            if prob.id in solved_ids:
                diff_stats[d]["solved"] += 1

        difficulty_breakdown: List[DifficultyBreakdownItem] = []
        for d_enum in (DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD):
            st = diff_stats[d_enum]
            s_rate = round((st["solved"] / max(st["attempted"], 1)) * 100, 1)
            difficulty_breakdown.append(
                DifficultyBreakdownItem(
                    difficulty=d_enum.value,
                    available=st["available"],
                    attempted=st["attempted"],
                    solved=st["solved"],
                    solve_rate=s_rate,
                )
            )

        # 8. Recent Performance (Last 10 submissions)
        recent_sub_stmt = (
            select(Submission)
            .where(
                Submission.user_id == user.id,
                Submission.problem_id.in_(company_problem_ids),
            )
            .order_by(Submission.created_at.desc())
            .limit(10)
        )
        recent_sub_res = await self.db.execute(recent_sub_stmt)
        recent_subs = recent_sub_res.scalars().all()
        recent_acc_rate = (
            (len([s for s in recent_subs if s.status == "ACCEPTED"]) / max(len(recent_subs), 1)) * 100
            if recent_subs
            else 50.0
        )

        # 9. Score Formula Components (0-100)
        problem_cov = (solved_count / max(total_available, 1)) * 100
        topic_cov = (covered_topics_count / max(len(topic_map), 1)) * 100
        success_rate = (solved_count / max(attempted_count, 1)) * 100

        # Skill-calibrated difficulty coverage
        user_skill = user.skill_level or SkillLevel.BEGINNER
        easy_sol = diff_stats[DifficultyLevel.EASY]["solved"]
        med_sol = diff_stats[DifficultyLevel.MEDIUM]["solved"]
        hard_sol = diff_stats[DifficultyLevel.HARD]["solved"]

        if user_skill == SkillLevel.BEGINNER:
            diff_cov = min(100.0, (easy_sol * 30 + med_sol * 20))
        elif user_skill == SkillLevel.INTERMEDIATE:
            diff_cov = min(100.0, (easy_sol * 15 + med_sol * 25 + hard_sol * 20))
        else:
            diff_cov = min(100.0, (med_sol * 20 + hard_sol * 30))

        raw_score = (
            0.30 * problem_cov
            + 0.25 * topic_cov
            + 0.20 * diff_cov
            + 0.15 * success_rate
            + 0.10 * recent_acc_rate
        )

        prep_score = int(min(100, max(0, round(raw_score))))

        if prep_score < 40:
            prep_status = "STARTING"
            conf_msg = "Starting company-specific preparation baseline."
        elif prep_score < 75:
            prep_status = "DEVELOPING"
            conf_msg = "Developing steady progress across company target topics."
        else:
            prep_status = "WELL_PREPARED"
            conf_msg = "Strong preparation coverage across target company topics."

        # 10. Strengths, Focus Areas & Recommended Next Steps
        strengths = []
        focus_areas = []

        strong_topics = [tb.topic_name for tb in topic_breakdown if tb.status == "STRONG"]
        if strong_topics:
            strengths.append(f"Strong performance in {', '.join(strong_topics[:2])}.")
        if easy_sol > 0:
            strengths.append("Established foundational problem-solving accuracy.")

        weak_topics = [tb.topic_name for tb in topic_breakdown if tb.status in ("NEEDS_PRACTICE", "NOT_STARTED")]
        if weak_topics:
            focus_areas.append(f"Low practice coverage in {', '.join(weak_topics[:2])}.")
        if diff_stats[DifficultyLevel.MEDIUM]["solved"] == 0:
            focus_areas.append("Limited Medium-level problem exposure.")

        if not strengths:
            strengths = ["Active practice profile initiated."]
        if not focus_areas:
            focus_areas = ["Maintain practice consistency."]

        unsolved_company_problems = [p for p in company_problems if p.id not in solved_ids]
        next_steps = [f"Solve {p.title} ({p.difficulty.value})" for p in unsolved_company_problems[:3]]

        # 11. Optional AI Explanation Generation
        ai_exp = None
        if settings.AI_ENABLED and self.ai_service:
            try:
                ai_exp = f"Your CodeTarget preparation score of {prep_score}/100 reflects {solved_count} solved problems out of {total_available} company-relevant questions. Focus next on strengthening {weak_topics[0] if weak_topics else 'Medium-level problems'}."
            except Exception as e:
                logger.warning(f"AI explanation fallback: {e}")

        return CompanyPreparationResponse(
            company=company_info,
            preparation_score=prep_score,
            status=prep_status,
            confidence_message=conf_msg,
            coverage=CoverageMetrics(
                overall=round(problem_cov, 1),
                topics=round(topic_cov, 1),
                difficulty=round(diff_cov, 1),
            ),
            problems=ProblemCounts(
                available=total_available,
                attempted=attempted_count,
                solved=solved_count,
            ),
            topic_breakdown=topic_breakdown,
            difficulty_breakdown=difficulty_breakdown,
            strengths=strengths,
            focus_areas=focus_areas,
            recommended_next_steps=next_steps,
            ai_explanation=ai_exp,
        )

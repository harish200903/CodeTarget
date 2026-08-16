import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user import User, SkillLevel
from app.models.problem import Problem, Topic, ProblemCompany, ProblemTopic, DifficultyLevel
from app.models.submission import Submission, UserProblemProgress, ProgressStatus
from app.schemas.problem import ProblemListItemOut
from app.schemas.ai import (
    RecommendationItem,
    RecommendationListResponse,
    AIRecommendationResponse,
)
from app.services.ai.base import AIService
from app.services.ai.exceptions import AIServiceError

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Hybrid deterministic and AI-assisted practice recommendation engine."""

    def __init__(self, db: AsyncSession, ai_service: Optional[AIService] = None):
        self.db = db
        self.ai_service = ai_service

    async def get_recommendations(
        self,
        user: User,
        limit: int = 5,
    ) -> RecommendationListResponse:
        """Generates personalized practice problem recommendations for a user."""
        # 1. Fetch solved problem IDs for user exclusion
        solved_stmt = select(UserProblemProgress.problem_id).where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.status == ProgressStatus.SOLVED,
        )
        solved_res = await self.db.execute(solved_stmt)
        solved_problem_ids = set(solved_res.scalars().all())

        # 2. Fetch attempted problem IDs
        attempted_stmt = select(UserProblemProgress.problem_id).where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.status == ProgressStatus.ATTEMPTED,
        )
        attempted_res = await self.db.execute(attempted_stmt)
        attempted_problem_ids = set(attempted_res.scalars().all())

        # 3. Detect weak topics & learning profile from submission history
        weak_topics: List[str] = []

        # Fetch recent submissions
        submissions_stmt = (
            select(Submission)
            .where(Submission.user_id == user.id)
            .order_by(Submission.created_at.desc())
            .limit(50)
        )
        sub_res = await self.db.execute(submissions_stmt)
        recent_submissions = sub_res.scalars().all()

        if recent_submissions:
            # Map recent failed problem submissions to topic weaknesses
            failed_problem_ids = {
                s.problem_id for s in recent_submissions if s.status != "ACCEPTED"
            }
            if failed_problem_ids:
                failed_topics_stmt = (
                    select(Topic.name)
                    .join(ProblemTopic, ProblemTopic.topic_id == Topic.id)
                    .where(ProblemTopic.problem_id.in_(failed_problem_ids))
                    .distinct()
                )
                failed_topics_res = await self.db.execute(failed_topics_stmt)
                weak_topics = list(failed_topics_res.scalars().all())

        # 4. Target Companies
        primary_company_id = None
        target_company_ids = []
        company_names = []

        if user.target_companies:
            for tc in user.target_companies:
                target_company_ids.append(tc.company_id)
                company_names.append(tc.company.name)
                if tc.priority == 1:
                    primary_company_id = tc.company_id

        # 5. Query candidate problems (Exclude solved problems)
        query = (
            select(Problem)
            .where(Problem.is_active == True)
            .options(
                selectinload(Problem.topic_associations).selectinload(ProblemTopic.topic),
                selectinload(Problem.company_associations).selectinload(ProblemCompany.company),
            )
        )

        if solved_problem_ids:
            query = query.where(Problem.id.not_in(solved_problem_ids))


        res = await self.db.execute(query)
        candidate_problems = res.scalars().all()

        if not candidate_problems:
            return RecommendationListResponse(
                items=[],
                focus_topics=weak_topics,
                source="deterministic",
            )

        # 6. Score candidate problems deterministically
        scored_candidates = []
        for problem in candidate_problems:
            score = 0
            reason_type = "COMPANY_PREPARATION"
            reason_text = "Matches your target company preparation profile."

            prob_company_ids = [pc.company_id for pc in problem.company_associations]
            prob_topic_names = [pt.topic.name for pt in problem.topic_associations]

            # Signal 1: Company Relevance (0-30 pts)
            if primary_company_id and primary_company_id in prob_company_ids:
                score += 30
                reason_type = "COMPANY_PREPARATION"
                reason_text = "Matches topics relevant to your primary target company preparation."
            elif any(cid in target_company_ids for cid in prob_company_ids):
                score += 15
                reason_type = "COMPANY_PREPARATION"
                reason_text = "Matches your selected target companies."

            # Signal 2: Topic Weakness (0-30 pts)
            matching_weak = [t for t in prob_topic_names if t in weak_topics]
            if matching_weak:
                score += 30
                reason_type = "WEAK_TOPIC"
                reason_text = f"Strengthens your {matching_weak[0]} fundamentals based on recent practice."

            # Signal 3: Difficulty Fit (0-20 pts)
            user_skill = user.skill_level or SkillLevel.BEGINNER
            if user_skill == SkillLevel.BEGINNER:
                if problem.difficulty == DifficultyLevel.EASY:
                    score += 20
                elif problem.difficulty == DifficultyLevel.MEDIUM:
                    score += 10
            elif user_skill == SkillLevel.INTERMEDIATE:
                if problem.difficulty == DifficultyLevel.MEDIUM:
                    score += 20
                else:
                    score += 10
            elif user_skill == SkillLevel.ADVANCED:
                if problem.difficulty == DifficultyLevel.HARD:
                    score += 20
                elif problem.difficulty == DifficultyLevel.MEDIUM:
                    score += 15

            # Signal 4: Attempted Reinforcement (0-10 pts)
            if problem.id in attempted_problem_ids:
                score += 10
                if reason_type != "WEAK_TOPIC":
                    reason_type = "REINFORCEMENT"
                    reason_text = "You previously attempted this pattern. Recommended for reinforcement."

            # Signal 5: Curated Quality Boost (0-10 pts)
            if any(pc.source_classification in ("CURATED", "OFFICIAL") for pc in problem.company_associations):
                score += 10

            scored_candidates.append({
                "problem": problem,
                "score": min(score, 100),
                "reason_type": reason_type,
                "reason_text": reason_text,
                "topic_names": prob_topic_names,
            })

        # Sort candidate pool descending by deterministic score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_pool = scored_candidates[: max(limit * 2, 10)]

        # 7. AI Prioritization Step (if AI_ENABLED and ai_service available)
        final_items = []
        source = "deterministic"

        if settings.AI_ENABLED and self.ai_service and top_pool:
            try:
                available_metadata = [
                    {
                        "id": str(c["problem"].id),
                        "title": c["problem"].title,
                        "difficulty": c["problem"].difficulty.value,
                        "score": c["score"],
                    }
                    for c in top_pool
                ]

                ai_res: AIRecommendationResponse = await self.ai_service.generate_recommendation(
                    target_companies=company_names or ["Top Tech"],
                    skill_level=user.skill_level.value if user.skill_level else "BEGINNER",
                    weak_topics=weak_topics or ["Arrays", "Hashing"],
                    available_problems=available_metadata,
                )

                # Strict Validation: Verify AI returned valid problem IDs in top_pool
                valid_pool_map = {str(c["problem"].id): c for c in top_pool}
                validated_items = []

                for recommended_id in ai_res.recommended_problem_ids:
                    if recommended_id in valid_pool_map:
                        item_data = valid_pool_map[recommended_id]
                        validated_items.append(item_data)

                if validated_items:
                    top_pool = validated_items
                    source = "ai"
            except Exception as e:
                logger.warning(f"AI recommendation prioritization fallback to deterministic: {e}")

        # 8. Build final recommendation response items
        for candidate in top_pool[:limit]:
            prob = candidate["problem"]
            item_schema = RecommendationItem(
                problem=ProblemListItemOut(
                    id=prob.id,
                    title=prob.title,
                    slug=prob.slug,
                    difficulty=prob.difficulty,
                    category=prob.category,
                    topics=[pt.topic for pt in prob.topic_associations],
                    companies=prob.company_associations,
                    user_status=ProgressStatus.ATTEMPTED if prob.id in attempted_problem_ids else ProgressStatus.UNATTEMPTED,
                    is_bookmarked=False,
                ),
                reason=candidate["reason_text"],
                reason_type=candidate["reason_type"],
                score=candidate["score"],
            )
            final_items.append(item_schema)

        # Focus topics list
        all_focus_topics = list(set(weak_topics + [t for item in final_items for t in [top.name for top in item.problem.topics]]))[:5]

        return RecommendationListResponse(
            items=final_items,
            focus_topics=all_focus_topics,
            source=source,
        )

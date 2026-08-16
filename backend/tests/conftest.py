import asyncio
import pytest
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.company import Company
from app.models.problem import Problem, Topic, ProblemCompany, ProblemTopic, TestCase, Hint, DifficultyLevel
from app.db.seed_data import DSA_TOPICS, PROBLEMS_DATA

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create all tables and seed initial companies, topics, problems, test cases, and hints in test DB."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # 1. Seed Companies
        company_map = {}
        companies_seed = [
            Company(id=uuid.uuid4(), name="TCS", slug="tcs", description="TCS Recruiter", tier="Service"),
            Company(id=uuid.uuid4(), name="Cognizant", slug="cognizant", description="Cognizant Recruiter", tier="Service"),
            Company(id=uuid.uuid4(), name="Infosys", slug="infosys", description="Infosys Recruiter", tier="Service"),
            Company(id=uuid.uuid4(), name="Accenture", slug="accenture", description="Accenture Recruiter", tier="Service"),
            Company(id=uuid.uuid4(), name="Wipro", slug="wipro", description="Wipro Recruiter", tier="Service"),
            Company(id=uuid.uuid4(), name="Deloitte", slug="deloitte", description="Deloitte Recruiter", tier="Consulting"),
            Company(id=uuid.uuid4(), name="Capgemini", slug="capgemini", description="Capgemini Recruiter", tier="Service"),
            Company(id=uuid.uuid4(), name="Zoho", slug="zoho", description="Zoho Product Recruiter", tier="Product"),
            Company(id=uuid.uuid4(), name="Amazon", slug="amazon", description="Amazon Tech Recruiter", tier="Top Tech"),
            Company(id=uuid.uuid4(), name="Microsoft", slug="microsoft", description="Microsoft Tech Recruiter", tier="Top Tech"),
        ]
        session.add_all(companies_seed)
        await session.flush()
        for c in companies_seed:
            company_map[c.slug] = c.id

        # 2. Seed DSA Topics
        topic_map = {}
        for t in DSA_TOPICS:
            top_obj = Topic(id=uuid.uuid4(), name=t["name"], slug=t["slug"], description=t["description"])
            session.add(top_obj)
            topic_map[t["slug"]] = top_obj.id
        await session.flush()

        # 3. Seed Problems, Test Cases, Hints
        for p_data in PROBLEMS_DATA:
            prob_obj = Problem(
                id=uuid.uuid4(),
                title=p_data["title"],
                slug=p_data["slug"],
                description_markdown=p_data["description_markdown"],
                difficulty=DifficultyLevel[p_data["difficulty"]],
                category=p_data["category"],
                constraints_text=p_data["constraints_text"],
                starter_code=p_data["starter_code"],
                solution_editorial=p_data["solution_editorial"]
            )
            session.add(prob_obj)
            await session.flush()

            # Topics
            for t_slug in p_data["topics"]:
                if t_slug in topic_map:
                    session.add(ProblemTopic(id=uuid.uuid4(), problem_id=prob_obj.id, topic_id=topic_map[t_slug]))

            # Companies
            for c_slug in p_data["companies"]:
                if c_slug in company_map:
                    session.add(ProblemCompany(
                        id=uuid.uuid4(),
                        problem_id=prob_obj.id,
                        company_id=company_map[c_slug],
                        frequency_weight=1.0,
                        recency_window="Last 12 Months",
                        round_type="ONLINE_ASSESSMENT",
                        source_classification="CURATED"
                    ))

            # Sample Test Cases
            for tc in p_data["sample_test_cases"]:
                session.add(TestCase(
                    id=uuid.uuid4(),
                    problem_id=prob_obj.id,
                    input_data=tc["input"],
                    expected_output=tc["expected_output"],
                    is_sample=True,
                    time_limit_ms=2000,
                    memory_limit_mb=256
                ))

            # Hidden Test Cases
            for tc in p_data["hidden_test_cases"]:
                session.add(TestCase(
                    id=uuid.uuid4(),
                    problem_id=prob_obj.id,
                    input_data=tc["input"],
                    expected_output=tc["expected_output"],
                    is_sample=False,
                    time_limit_ms=2000,
                    memory_limit_mb=256
                ))

            # Hints
            for h in p_data["hints"]:
                session.add(Hint(
                    id=uuid.uuid4(),
                    problem_id=prob_obj.id,
                    step_number=h["step"],
                    title=h["title"],
                    content_markdown=h["content"]
                ))

        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override for test database session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
async def test_user_token(async_client: AsyncClient) -> str:
    """Fixture registering a new user and returning a valid JWT access token."""
    reg_payload = {
        "full_name": "Test Runner Candidate",
        "email": f"candidate_{uuid.uuid4().hex[:8]}@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    response = await async_client.post("/api/v1/auth/register", json=reg_payload)
    return response.json()["access_token"]

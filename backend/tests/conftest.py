import asyncio
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.company import Company, SourceClassification
import uuid
from datetime import datetime, timezone

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
    """Create all tables and seed initial companies in test DB before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed 10 initial recruiter companies into test DB
    async with TestingSessionLocal() as session:
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

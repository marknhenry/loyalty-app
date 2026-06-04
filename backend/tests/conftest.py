"""pytest fixtures shared across all test modules."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_db
from app.models import APIKey, ExchangeRate, Member, MemberRole
from app.utils import (
    create_access_token,
    generate_api_key,
    hash_api_key,
    hash_password,
)

# ---------------------------------------------------------------------------
# Async test configuration
# ---------------------------------------------------------------------------

pytest_plugins = ["pytest_asyncio"]


# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests (no PostgreSQL required)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_test_session_factory = async_sessionmaker(
    _test_engine, expire_on_commit=False, class_=AsyncSession
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with _test_session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with DB override so tests use in-memory SQLite."""
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Member fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def member(db: AsyncSession) -> Member:
    m = Member(
        email="alice@example.com",
        hashed_password=hash_password("secret123"),
        full_name="Alice",
        role=MemberRole.member,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


@pytest_asyncio.fixture
async def admin_member(db: AsyncSession) -> Member:
    m = Member(
        email="admin@example.com",
        hashed_password=hash_password("adminpass"),
        full_name="Admin User",
        role=MemberRole.admin,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


@pytest_asyncio.fixture
async def second_member(db: AsyncSession) -> Member:
    m = Member(
        email="bob@example.com",
        hashed_password=hash_password("bobpass"),
        full_name="Bob",
        role=MemberRole.member,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def member_token(m: Member) -> str:
    return create_access_token(subject=m.id, role=m.role.value)


def admin_token(m: Member) -> str:
    return create_access_token(subject=m.id, role="admin")


# ---------------------------------------------------------------------------
# API key fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def api_key(db: AsyncSession) -> tuple[str, APIKey]:
    """Returns (plain_key, APIKey model) for test ingestion calls."""
    plain = generate_api_key()
    key_obj = APIKey(key_hash=hash_api_key(plain), partner_name="Test Partner")
    db.add(key_obj)
    await db.commit()
    await db.refresh(key_obj)
    return plain, key_obj


# ---------------------------------------------------------------------------
# Exchange rate fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def standard_rate(db: AsyncSession) -> ExchangeRate:
    rate = ExchangeRate(name="standard", rate=1.0, min_amount=1, is_active=True)
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return rate

"""
Shared pytest fixtures for the Concurrent POS System test suite.

Strategy: Each test gets its own DB session that is wrapped in a transaction
which is rolled back after the test completes. This guarantees test isolation
without needing a separate test database.

Flow per test:
  1. Open a real connection to Neon
  2. BEGIN transaction
  3. Yield a session bound to that connection
  4. ROLLBACK (all inserts/updates the test made vanish)
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.main import app

# ---------------------------------------------------------------------------
# Build a test engine (same Neon DB, NullPool so we manage connections ourselves)
# ---------------------------------------------------------------------------
from sqlalchemy.pool import NullPool

_raw_url = settings.DATABASE_URL
_connect_args: dict = {}
if "ssl=require" in _raw_url:
    _connect_args["ssl"] = "require"
    _raw_url = _raw_url.replace("?ssl=require", "").replace("&ssl=require", "")

test_engine = create_async_engine(
    _raw_url,
    connect_args=_connect_args,
    poolclass=NullPool,
    echo=False,
)


# ---------------------------------------------------------------------------
# Per-test DB session with automatic rollback
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db_session():
    """Yields an AsyncSession bound to a transaction that rolls back after the test."""
    async with test_engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


# ---------------------------------------------------------------------------
# HTTPX AsyncClient with the get_db dependency overridden
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """AsyncClient that talks to the FastAPI app and uses the rollback session."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

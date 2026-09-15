from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine
# SSL connect_args are needed for cloud providers like Neon that require TLS.
# asyncpg uses ssl="require" via connect_args rather than the query string.
# ---------------------------------------------------------------------------
_connect_args: dict = {}
if "ssl=require" in settings.DATABASE_URL:
    _connect_args["ssl"] = "require"

# Strip the ssl param from the URL — asyncpg takes it via connect_args instead
_db_url = settings.DATABASE_URL.replace("?ssl=require", "").replace("&ssl=require", "")

engine = create_async_engine(
    _db_url,
    connect_args=_connect_args,
    echo=settings.APP_ENV == "development",
    pool_pre_ping=True,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# ---------------------------------------------------------------------------
# Declarative base — all models inherit from this
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

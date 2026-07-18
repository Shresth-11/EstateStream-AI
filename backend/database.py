from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from backend.config import settings

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Async Engine for FastAPI routes and background tasks
# Handles both PostgreSQL (postgresql+asyncpg://) and SQLite (sqlite+aiosqlite://)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    # SQLite requires check_same_thread = False
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Synchronous Engine (used by Alembic and sync seed utilities)
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL_SYNC else {},
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initializes tables asynchronously (useful for rapid dev/testing)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

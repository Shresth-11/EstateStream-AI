from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from backend.config import settings

from sqlalchemy.pool import NullPool

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Async Engine for FastAPI routes and background tasks
# Handles both PostgreSQL (postgresql+asyncpg://) and SQLite (sqlite+aiosqlite://)
_async_engine_kwargs = {}
if "sqlite" in settings.DATABASE_URL:
    _async_engine_kwargs["connect_args"] = {"check_same_thread": False}
    _async_engine_kwargs["poolclass"] = NullPool

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    **_async_engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Synchronous Engine (used by Alembic and sync seed utilities)
_sync_engine_kwargs = {}
_sync_url = settings.DATABASE_URL_SYNC
if "sqlite" in _sync_url:
    _sync_engine_kwargs["connect_args"] = {"check_same_thread": False}
    _sync_engine_kwargs["poolclass"] = NullPool
elif _sync_url.startswith("postgresql://"):
    _sync_url = _sync_url.replace("postgresql://", "postgresql+psycopg2://", 1)

sync_engine = create_engine(
    _sync_url,
    echo=False,
    future=True,
    **_sync_engine_kwargs,
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
    """Initializes tables asynchronously and auto-seeds initial properties and demo leads."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-seed if tables are empty (guarantees leads and inventory appear out-of-the-box)
    from sqlalchemy import select, func
    from backend.models import Property, Lead, Conversation
    from backend.seed_data import SAMPLE_PROPERTIES, SAMPLE_LEADS

    async with AsyncSessionLocal() as session:
        try:
            prop_count_res = await session.execute(select(func.count(Property.id)))
            prop_count = prop_count_res.scalar() or 0
            if prop_count == 0:
                for p_data in SAMPLE_PROPERTIES:
                    session.add(Property(**p_data))
                await session.commit()

            lead_count_res = await session.execute(select(func.count(Lead.id)))
            lead_count = lead_count_res.scalar() or 0
            if lead_count == 0:
                for item in SAMPLE_LEADS:
                    lead_data = item["lead"]
                    conv_data = item["conversation"]
                    lead_obj = Lead(**lead_data)
                    session.add(lead_obj)
                    await session.flush()

                    conv_obj = Conversation(
                        lead_id=lead_obj.id,
                        duration_seconds=conv_data.get("duration_seconds", 60),
                        outcome=conv_data.get("outcome", "qualified"),
                        summary=conv_data.get("summary", ""),
                        transcript=conv_data.get("transcript", []),
                    )
                    session.add(conv_obj)
                await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Warning: database auto-seed encountered: {e}")

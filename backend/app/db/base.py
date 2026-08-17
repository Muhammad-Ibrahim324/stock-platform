"""Database engine and session setup.

SQLite by default (see `Settings.database_url`) — zero config, a single
file, good enough for local dev and this demo. The models below use no
SQLite-specific types, so pointing `DATABASE_URL` at Postgres in
production is a config change, not a code change.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        _engine = create_async_engine(settings.database_url, connect_args=connect_args)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def init_db() -> None:
    """Create tables if they don't exist yet.

    A real production deployment with an evolving schema would use Alembic
    migrations instead of this — `create_all` is additive-only and won't
    handle altering existing tables. For this project's current scope
    (fresh schema, no prior deployed version to migrate from) that
    trade-off is fine; it's called out here so it's not a silent gap.
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session

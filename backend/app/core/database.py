from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.base import Base
from backend.app.database import _get_postgres_url, _get_psycopg_connect_args


@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine:
    """Use the LL-05 URL/TLS policy for both sync and async Psycopg connections."""
    return create_async_engine(
        _get_postgres_url(),
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=2,
        pool_recycle=1800,
        connect_args=_get_psycopg_connect_args(),
    )


@lru_cache(maxsize=1)
def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_async_engine(), expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_sessionmaker()() as session:
        yield session


__all__ = ["Base", "get_async_engine", "get_async_sessionmaker", "get_db"]

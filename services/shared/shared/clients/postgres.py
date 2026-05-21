"""Async SQLAlchemy engine + session factory for every service that touches Postgres.

The critical detail: we disable asyncpg's prepared-statement cache and
SQLAlchemy's prepared-statement cache because Supabase's transaction-mode
pooler (Supavisor on port 6543) reuses backends across client connections.
Without disabling, asyncpg's auto-generated `__asyncpg_stmt_N__` collides
with the same name from a previous client. We learned this in Phase 1.5 —
see developing_process.md §1.5 "11. ders".
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_async_engine_for_service(postgres_url: str, *, echo: bool = False) -> AsyncEngine:
    """Build the async engine with Supavisor-pooler-safe settings.

    Two caches must be disabled to survive Supabase's transaction-mode pooler
    reusing backends across clients:

      1. SQLAlchemy's prepared-statement cache (dialect level). Set via URL
         query: ``?prepared_statement_cache_size=0``. The asyncpg dialect
         picks this up from the URL.

      2. asyncpg's own statement cache (driver level). Set via ``connect_args``:
         ``{"statement_cache_size": 0}``.

    Missing either re-introduces ``DuplicatePreparedStatementError`` on the
    second connection that lands on a previously-used backend session.

    Args:
        postgres_url: must start with ``postgresql+asyncpg://``
        echo: SQL logging — True only for local debug.
    """
    # Force-append the SQLAlchemy-level cache disable to the URL.
    sep = "&" if "?" in postgres_url else "?"
    url_with_cache_off = (
        postgres_url
        if "prepared_statement_cache_size" in postgres_url
        else f"{postgres_url}{sep}prepared_statement_cache_size=0"
    )

    return create_async_engine(
        url_with_cache_off,
        echo=echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={
            "statement_cache_size": 0,  # asyncpg-level cache off
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build a per-request session factory.

    Sessions are short-lived: open at request start, closed in the dep's
    `finally`. `expire_on_commit=False` lets us return ORM objects from
    endpoints without lazy-load surprises after the session closes.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def session_dep(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency adapter.

    Usage in a service:

        engine = create_async_engine_for_service(settings.postgres_url)
        SessionFactory = create_session_factory(engine)

        async def get_session() -> AsyncIterator[AsyncSession]:
            async for s in session_dep(SessionFactory):
                yield s
    """
    async with session_factory() as session:
        yield session

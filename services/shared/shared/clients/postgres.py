"""Async SQLAlchemy engine + session factory for every service that touches Postgres.

THE pooler-safety story (learned the hard way across Phase 1.5, Phase 2.8,
and Phase 4):

  Supabase's transaction-mode pooler (Supavisor on port 6543) multiplexes
  many client connections onto fewer backend Postgres sessions. Backends
  are recycled between clients on transaction boundaries. The problem:
  *prepared statements are session-level* on the backend, so when a client
  prepares ``_sqla_1`` and the pooler later hands that backend to a new
  client, the new client's "fresh" ``_sqla_1`` collides
  (``DuplicatePreparedStatementError``).

  Two settings together make us pooler-safe:

    1. ``statement_cache_size=0`` (asyncpg connect_args) — disables asyncpg's
       own auto-named prepared statements (``__asyncpg_stmt_N__``).

    2. ``prepared_statement_name_func`` (asyncpg connect_args) — gives every
       SQLAlchemy-issued ``connection.prepare()`` a unique UUID name. Names
       never collide no matter how the pooler shuffles backends. Each
       prepared statement leaks one entry on its backend until session
       close — acceptable for low-volume demos, would be revisited with
       a stricter pool budget in production.

  The ``prepared_statement_cache_size=0`` URL/engine kwarg is documented
  but only switches whether SQLAlchemy *caches* the resulting prepared
  statement — the dialect still calls ``prepare(..., name=_sqla_N)`` with
  deterministic counter-based names. Insufficient on its own.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _unique_prepared_name() -> str:
    """Per-call unique prepared-statement name. See module docstring."""
    return f"__asyncpg_{uuid4().hex}__"


def create_async_engine_for_service(postgres_url: str, *, echo: bool = False) -> AsyncEngine:
    """Build the async engine with Supavisor-pooler-safe settings.

    Args:
        postgres_url: must start with ``postgresql+asyncpg://``
        echo: SQL logging — True only for local debug.
    """
    return create_async_engine(
        postgres_url,
        echo=echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_name_func": _unique_prepared_name,
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

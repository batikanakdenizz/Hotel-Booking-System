"""Dependencies — Postgres session, Redis client, optional Firebase auth.

Search-service auth is OPTIONAL: anonymous gets base prices, authenticated
gets the 15% discount applied at response-build time.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.auth.deps import FirebaseClaims, optional_current_user


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
OptionalUserDep = Annotated[FirebaseClaims | None, Depends(optional_current_user)]

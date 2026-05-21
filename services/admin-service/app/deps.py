"""FastAPI dependencies — wired directly here (not via shared.auth.deps builders)
so FastAPI's introspection sees plain top-level `async def`s rather than nested
closures returned from a factory. This avoids a 422 mis-detection where the
inner `user` parameter was treated as a query string instead of a sub-dep.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.auth.deps import FirebaseClaims, _get_or_create_user_impl, get_current_user
from shared.models import User


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


async def get_or_create_user(
    claims: Annotated[FirebaseClaims, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    return await _get_or_create_user_impl(session, claims)


async def require_admin(
    current_user: Annotated[User, Depends(get_or_create_user)],
) -> User:
    if current_user.role != "hotel_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return current_user


# Type aliases — endpoint signatures become 1-line readable.
SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
ClaimsDep = Annotated[FirebaseClaims, Depends(get_current_user)]
AdminDep = Annotated[User, Depends(require_admin)]

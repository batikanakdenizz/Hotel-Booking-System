"""Dependencies — session, RabbitMQ connection, auth chain."""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from aio_pika.abc import AbstractRobustConnection
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.auth.deps import FirebaseClaims, _get_or_create_user_impl, get_current_user
from shared.models import User


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


async def get_rabbitmq(request: Request) -> AbstractRobustConnection:
    return request.app.state.rabbitmq


async def get_or_create_user(
    claims: Annotated[FirebaseClaims, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    return await _get_or_create_user_impl(session, claims)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
RabbitMQDep = Annotated[AbstractRobustConnection, Depends(get_rabbitmq)]
UserDep = Annotated[User, Depends(get_or_create_user)]

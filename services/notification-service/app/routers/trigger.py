"""POST /trigger/nightly — invoked by Google Cloud Scheduler.

Authenticates via a shared secret header (X-Cron-Secret). Not Firebase —
the scheduler doesn't have a user identity.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.workers.occupancy import run_nightly_check

router = APIRouter(tags=["trigger"])


def _verify_cron_secret(x_cron_secret: Annotated[str | None, Header()] = None) -> None:
    if x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad cron secret")


@router.post("/trigger/nightly", dependencies=[Depends(_verify_cron_secret)])
async def nightly_endpoint(request: Request) -> dict:
    """Runs the low-availability check, returns a summary."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    email = request.app.state.email_client
    async with factory() as session:
        return await run_nightly_check(session, email)

"""ai-agent-service entry — lifespan boots a shared httpx client.

No Firebase init (agent doesn't verify tokens — gateway does). No Postgres.
No RabbitMQ. The service is a thin orchestrator over Groq + the gateway.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.config import settings
from app.routers import chat
from shared.logging import configure_logging

logger = configure_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting", port=8006, gateway=settings.gateway_url)
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5.0, read=60.0, write=60.0, pool=5.0)
    )
    logger.info("service_started")
    try:
        yield
    finally:
        logger.info("service_stopping")
        await app.state.http_client.aclose()
        logger.info("service_stopped")


app = FastAPI(title="Hotel Booking — AI Agent Service", version="0.1.0", lifespan=lifespan)
app.include_router(chat.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}

"""search-service entry point.

Lifespan boots Firebase (for optional token verification on the discount path),
the async Postgres engine, and the Redis client.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import search
from shared.auth.firebase import init_firebase_app
from shared.clients.postgres import create_async_engine_for_service, create_session_factory
from shared.clients.redis import create_redis_client
from shared.logging import configure_logging

logger = configure_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting", port=8002)

    init_firebase_app(
        project_id=settings.firebase_project_id,
        service_account_path=settings.firebase_service_account_path,
        service_account_json=settings.firebase_service_account_json,
    )

    engine = create_async_engine_for_service(settings.postgres_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.redis = create_redis_client(settings.redis_url)

    logger.info("service_started")
    try:
        yield
    finally:
        logger.info("service_stopping")
        await app.state.redis.aclose()
        await engine.dispose()
        logger.info("service_stopped")


app = FastAPI(
    title="Hotel Booking — Search Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(search.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}

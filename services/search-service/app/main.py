"""Search service — Phase 0 stub.

Real implementation (Postgres availability query + Redis hotel-detail cache-aside +
runtime 15% discount) lands in Phase 4. Cache invalidation is admin-service's job.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.logging import configure_logging

SERVICE_NAME = "search-service"
logger = configure_logging(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting")
    yield
    logger.info("service_stopping")


app = FastAPI(title="Hotel Booking — Search Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}

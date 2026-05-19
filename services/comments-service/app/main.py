"""Comments service — Phase 0 stub.

Real implementation (MongoDB comment CRUD + 5-dimensional rating aggregation
matching the PDF mockup) lands in Phase 6.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.logging import configure_logging

SERVICE_NAME = "comments-service"
logger = configure_logging(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting")
    yield
    logger.info("service_stopping")


app = FastAPI(title="Hotel Booking — Comments Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}

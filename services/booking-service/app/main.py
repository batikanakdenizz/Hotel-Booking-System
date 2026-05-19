"""Booking service — Phase 0 stub.

Real implementation (transactional capacity decrease + durable/persistent RabbitMQ
publish with retry, see PROJECT_PLAN.md §3.3) lands in Phase 5.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.logging import configure_logging

SERVICE_NAME = "booking-service"
logger = configure_logging(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting")
    yield
    logger.info("service_stopping")


app = FastAPI(title="Hotel Booking — Booking Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}

"""Notification service — Phase 0 stub.

Real implementation lands in Phase 7:
  - RabbitMQ durable consumer for reservation.created events → Resend email
  - POST /trigger/nightly: low-capacity occupancy check + admin email
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.logging import configure_logging

SERVICE_NAME = "notification-service"
logger = configure_logging(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting")
    # Phase 7: spin up the RabbitMQ consumer as an asyncio background task here.
    yield
    logger.info("service_stopping")


app = FastAPI(title="Hotel Booking — Notification Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}

"""notification-service entry — RabbitMQ consumer + PG + Resend client.

No Firebase: /trigger/nightly uses X-Cron-Secret, RabbitMQ consumer doesn't
verify users (events come from booking-service over a trusted broker).
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import trigger
from app.services.email import EmailClient
from app.workers.consumer import consume_reservations
from shared.clients.postgres import create_async_engine_for_service, create_session_factory
from shared.clients.rabbitmq import create_rabbitmq_connection
from shared.logging import configure_logging

logger = configure_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting", port=8005)

    engine = create_async_engine_for_service(settings.postgres_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    app.state.rabbitmq = await create_rabbitmq_connection(settings.rabbitmq_url)
    app.state.email_client = EmailClient(
        api_key=settings.brevo_api_key,
        sender_email=settings.email_from,
        sender_name=settings.email_from_name,
    )

    # Start the consumer as a background task. Cancel cleanly on shutdown.
    stop_event = asyncio.Event()
    app.state.stop_event = stop_event
    consumer_task = asyncio.create_task(
        consume_reservations(app.state.rabbitmq, app.state.email_client, stop_event),
        name="rabbitmq_consumer",
    )
    app.state.consumer_task = consumer_task

    logger.info("service_started")
    try:
        yield
    finally:
        logger.info("service_stopping")
        stop_event.set()
        consumer_task.cancel()
        try:
            await consumer_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        await app.state.email_client.aclose()
        await app.state.rabbitmq.close()
        await engine.dispose()
        logger.info("service_stopped")


app = FastAPI(title="Hotel Booking — Notification Service", version="0.1.0", lifespan=lifespan)
app.include_router(trigger.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}

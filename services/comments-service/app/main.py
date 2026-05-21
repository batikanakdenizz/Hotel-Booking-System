"""comments-service entry — Mongo + Firebase, no Postgres."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import ASCENDING, DESCENDING

from app.config import settings
from app.routers import comments
from shared.auth.firebase import init_firebase_app
from shared.clients.mongo import create_mongo_client, get_database
from shared.logging import configure_logging

logger = configure_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting", port=8004)

    init_firebase_app(
        project_id=settings.firebase_project_id,
        service_account_path=settings.firebase_service_account_path,
        service_account_json=settings.firebase_service_account_json,
    )

    client = create_mongo_client(settings.mongo_url)
    app.state.mongo_client = client
    app.state.mongo_db = get_database(client, settings.mongo_db_name)

    # Indexes per Plan §5.2 — created on every boot, idempotent.
    collection = app.state.mongo_db["comments"]
    await collection.create_index([("hotel_id", ASCENDING), ("created_at", DESCENDING)])
    await collection.create_index([("user_id", ASCENDING)])
    logger.info("indexes_ensured")

    logger.info("service_started")
    try:
        yield
    finally:
        logger.info("service_stopping")
        client.close()
        logger.info("service_stopped")


app = FastAPI(title="Hotel Booking — Comments Service", version="0.1.0", lifespan=lifespan)
app.include_router(comments.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}

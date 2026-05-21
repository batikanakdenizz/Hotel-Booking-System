"""Motor (async PyMongo) client for comments-service."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


def create_mongo_client(mongo_url: str) -> AsyncIOMotorClient:
    """Single Motor client per service. Internally maintains a TCP pool.

    Atlas free tier limits the cluster to 500 connections total — Motor's
    default maxPoolSize of 100 is fine for a single service.
    serverSelectionTimeoutMS bounds startup failure: without it Motor waits
    30s before raising on DNS/auth issues.
    """
    return AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=10_000,
        # Atlas works best with snappy compression; PyMongo will negotiate.
        compressors="snappy,zlib",
    )


def get_database(client: AsyncIOMotorClient, db_name: str) -> AsyncIOMotorDatabase:
    """Convenience accessor — `client[db_name]` shorthand with type hints."""
    return client[db_name]

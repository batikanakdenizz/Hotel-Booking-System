"""Cache invalidation helpers — admin-service owns hotel:{id} key lifecycle.

Pattern: after every committing write that touches the hotels table,
the router calls `invalidate_hotel(redis, hotel_id)`. Search-service
reads from this cache and never invalidates. See Plan §3.5.
"""
from __future__ import annotations

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


async def invalidate_hotel(redis: Redis, hotel_id: str) -> None:
    """Drop the static hotel detail key. Safe to call when key doesn't exist."""
    deleted = await redis.delete(f"hotel:{hotel_id}")
    logger.info("cache_invalidated", scope="hotel", hotel_id=hotel_id, key_existed=bool(deleted))


async def invalidate_destination(redis: Redis, destination_lower: str) -> None:
    """Drop the destination → hotel_ids list (used when a hotel is created/destination changes)."""
    deleted = await redis.delete(f"destination:{destination_lower}:hotel_ids")
    logger.info("cache_invalidated", scope="destination", destination=destination_lower, key_existed=bool(deleted))

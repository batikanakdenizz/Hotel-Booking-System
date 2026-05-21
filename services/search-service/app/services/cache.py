"""Hotel-detail + destination-index cache-aside helpers.

Search-service ONLY reads + fills-on-miss. Invalidation is owned by
admin-service — see Plan §3.5. Cache contents are the static portion
of a hotel (id, name, description, address, lat/long, star_rating,
amenities, image_url + the room catalogue with base prices).
Availability is NEVER cached.
"""
from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

import structlog
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models import Hotel, Room

logger = structlog.get_logger(__name__)


# ---- Encoding ----------------------------------------------------------------

def _hotel_to_dict(hotel: Hotel, rooms: list[Room]) -> dict:
    """Snapshot the static parts of a hotel + its room catalogue."""
    return {
        "id": str(hotel.id),
        "name": hotel.name,
        "description": hotel.description,
        "destination": hotel.destination,
        "address": hotel.address,
        "latitude": hotel.latitude,
        "longitude": hotel.longitude,
        "star_rating": hotel.star_rating,
        "amenities": hotel.amenities,
        "image_url": hotel.image_url,
        "rooms": [
            {
                "id": str(r.id),
                "room_type": r.room_type,
                "capacity": r.capacity,
                "base_price_per_night": str(r.base_price_per_night),
                "total_rooms": r.total_rooms,
            }
            for r in rooms
        ],
    }


# ---- hotel:{id} -------------------------------------------------------------

async def get_hotel_detail(
    redis: Redis,
    session: AsyncSession,
    hotel_id: UUID,
    *,
    ttl_seconds: int,
) -> dict | None:
    """Cache-aside read. Returns the cached/freshly-loaded payload, or None if hotel doesn't exist.

    On miss: load hotel + its rooms eagerly, write to cache, return the dict.
    """
    key = f"hotel:{hotel_id}"
    raw = await redis.get(key)
    if raw is not None:
        logger.debug("cache_hit", key=key)
        return json.loads(raw)

    logger.debug("cache_miss", key=key)
    # No SQLAlchemy relationship is wired between Hotel and Room (we don't need
    # back-refs at write time), so we load rooms with a second query.
    hotel = (
        await session.execute(
            select(Hotel).where(Hotel.id == hotel_id, Hotel.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if hotel is None:
        return None

    rooms = list(
        (
            await session.execute(
                select(Room).where(Room.hotel_id == hotel_id).order_by(Room.created_at)
            )
        ).scalars().all()
    )
    payload = _hotel_to_dict(hotel, rooms)
    await redis.set(key, json.dumps(payload), ex=ttl_seconds)
    return payload


# ---- destination:{name_lower}:hotel_ids -------------------------------------

async def get_destination_hotel_ids(
    redis: Redis,
    session: AsyncSession,
    destination_lower: str,
    *,
    ttl_seconds: int,
) -> list[str]:
    """Cache-aside list of hotel UUIDs for a given destination (lowercased)."""
    key = f"destination:{destination_lower}:hotel_ids"
    raw = await redis.get(key)
    if raw is not None:
        logger.debug("cache_hit", key=key)
        return json.loads(raw)

    logger.debug("cache_miss", key=key)
    rows = (
        await session.execute(
            select(Hotel.id).where(
                Hotel.deleted_at.is_(None),
                Hotel.destination.ilike(destination_lower),  # case-insensitive
            )
        )
    ).scalars().all()
    ids = [str(r) for r in rows]
    await redis.set(key, json.dumps(ids), ex=ttl_seconds)
    return ids


# ---- Decimal helper for callers ----------------------------------------------

def to_decimal(value: str | Decimal) -> Decimal:
    """Cached prices come back as strings (JSON-safe). Cast cleanly."""
    return Decimal(value) if not isinstance(value, Decimal) else value

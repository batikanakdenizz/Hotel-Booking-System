"""Postgres availability query — always fresh, never cached."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Room, RoomAvailability


@dataclass(frozen=True)
class AvailableRoomRow:
    """One row of the availability query — bookable for the whole date range."""

    hotel_id: UUID
    room_id: UUID
    room_type: str
    capacity: int
    min_available: int  # smallest available_count seen across the range


async def query_available_rooms(
    session: AsyncSession,
    *,
    hotel_ids: list[UUID] | None,
    check_in: date,
    check_out: date,
    guests: int,
) -> list[AvailableRoomRow]:
    """Return rooms with availability >= 1 on EVERY day in [check_in, check_out).

    Date semantics match the booking flow: check_in inclusive, check_out exclusive
    (a stay from 2026-07-15 to 2026-07-18 = 3 nights = needs availability on
    Jul 15, 16, 17, not Jul 18).
    """
    if check_out <= check_in:
        return []
    nights = (check_out - check_in).days  # number of days needing availability

    stmt = (
        select(
            Room.hotel_id,
            Room.id.label("room_id"),
            Room.room_type,
            Room.capacity,
            func.min(RoomAvailability.available_count).label("min_available"),
        )
        .join(RoomAvailability, RoomAvailability.room_id == Room.id)
        .where(
            RoomAvailability.date >= check_in,
            RoomAvailability.date < check_out,
            Room.capacity >= guests,
        )
        .group_by(Room.id, Room.hotel_id, Room.room_type, Room.capacity)
        # Every night in the range must have a row, AND minimum availability > 0.
        .having(func.count(RoomAvailability.id) == nights)
        .having(func.min(RoomAvailability.available_count) > 0)
    )

    if hotel_ids is not None:
        stmt = stmt.where(Room.hotel_id.in_(hotel_ids))

    rows = (await session.execute(stmt)).all()
    return [
        AvailableRoomRow(
            hotel_id=r.hotel_id,
            room_id=r.room_id,
            room_type=r.room_type,
            capacity=r.capacity,
            min_available=r.min_available,
        )
        for r in rows
    ]

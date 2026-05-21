"""Booking + availability repository — pure async functions over AsyncSession."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Booking, Hotel, Room, RoomAvailability


async def find_booking_by_idempotency_key(session: AsyncSession, key: str) -> Booking | None:
    return (
        await session.execute(select(Booking).where(Booking.idempotency_key == key))
    ).scalar_one_or_none()


async def lock_availability_range(
    session: AsyncSession, *, room_id: UUID, check_in: date, check_out: date
) -> list[RoomAvailability]:
    """SELECT ... FOR UPDATE on availability rows for [check_in, check_out).

    Returns rows ordered by date so the caller can validate "every night present".
    Row locks serialize concurrent bookings of the same room/date — even READ
    COMMITTED isolation is sufficient.
    """
    stmt = (
        select(RoomAvailability)
        .where(
            RoomAvailability.room_id == room_id,
            RoomAvailability.date >= check_in,
            RoomAvailability.date < check_out,
        )
        .order_by(RoomAvailability.date)
        .with_for_update()
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_room_with_hotel(session: AsyncSession, room_id: UUID) -> tuple[Room, Hotel] | None:
    stmt = (
        select(Room, Hotel)
        .join(Hotel, Hotel.id == Room.hotel_id)
        .where(Room.id == room_id, Hotel.deleted_at.is_(None))
    )
    row = (await session.execute(stmt)).one_or_none()
    return None if row is None else (row[0], row[1])


async def insert_booking(session: AsyncSession, booking: Booking) -> Booking:
    session.add(booking)
    return booking


async def list_user_bookings(
    session: AsyncSession, *, user_id: UUID, offset: int, limit: int
) -> tuple[list[Booking], int]:
    base = (
        select(Booking)
        .where(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    count = select(func.count()).select_from(Booking).where(Booking.user_id == user_id)
    items = (await session.execute(base)).scalars().all()
    total = (await session.execute(count)).scalar_one()
    return list(items), total


async def get_booking(session: AsyncSession, booking_id: UUID) -> Booking | None:
    return (
        await session.execute(select(Booking).where(Booking.id == booking_id))
    ).scalar_one_or_none()

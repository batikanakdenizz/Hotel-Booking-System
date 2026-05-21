"""Hotel + Room CRUD against Postgres. Pure functions over AsyncSession."""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Hotel, Room, RoomAvailability


async def create_hotel(session: AsyncSession, *, data: dict) -> Hotel:
    hotel = Hotel(**data)
    session.add(hotel)
    await session.commit()
    await session.refresh(hotel)
    return hotel


async def list_hotels(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    include_deleted: bool = False,
) -> tuple[list[Hotel], int]:
    base = select(Hotel)
    count_base = select(func.count()).select_from(Hotel)
    if not include_deleted:
        base = base.where(Hotel.deleted_at.is_(None))
        count_base = count_base.where(Hotel.deleted_at.is_(None))
    base = base.order_by(Hotel.created_at.desc()).offset(offset).limit(limit)
    items = (await session.execute(base)).scalars().all()
    total = (await session.execute(count_base)).scalar_one()
    return list(items), total


async def get_hotel(session: AsyncSession, hotel_id: UUID, *, include_deleted: bool = False) -> Hotel | None:
    stmt = select(Hotel).where(Hotel.id == hotel_id)
    if not include_deleted:
        stmt = stmt.where(Hotel.deleted_at.is_(None))
    return (await session.execute(stmt)).scalar_one_or_none()


async def update_hotel(session: AsyncSession, hotel: Hotel, *, changes: dict) -> Hotel:
    for k, v in changes.items():
        setattr(hotel, k, v)
    await session.commit()
    await session.refresh(hotel)
    return hotel


async def soft_delete_hotel(session: AsyncSession, hotel: Hotel) -> None:
    hotel.deleted_at = func.now()
    await session.commit()


# ---- rooms -------------------------------------------------------------------

async def create_room(session: AsyncSession, *, hotel_id: UUID, data: dict) -> Room:
    room = Room(hotel_id=hotel_id, **data)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room


async def list_rooms(
    session: AsyncSession, *, hotel_id: UUID, offset: int, limit: int
) -> tuple[list[Room], int]:
    base = select(Room).where(Room.hotel_id == hotel_id).order_by(Room.created_at).offset(offset).limit(limit)
    count = select(func.count()).select_from(Room).where(Room.hotel_id == hotel_id)
    items = (await session.execute(base)).scalars().all()
    total = (await session.execute(count)).scalar_one()
    return list(items), total


async def get_room(session: AsyncSession, room_id: UUID) -> Room | None:
    return (await session.execute(select(Room).where(Room.id == room_id))).scalar_one_or_none()


# ---- room availability -------------------------------------------------------

async def upsert_availability_range(
    session: AsyncSession,
    *,
    room_id: UUID,
    start_date: date,
    end_date: date,
    available_count: int,
) -> int:
    """Upsert availability for every day in [start_date, end_date] inclusive.

    Uses ON CONFLICT (room_id, date) DO UPDATE — idempotent re-runs are safe.
    Returns the number of rows affected (= days in the range).
    """
    if end_date < start_date:
        raise ValueError("end_date must be >= start_date")

    rows = []
    current = start_date
    while current <= end_date:
        rows.append({"room_id": room_id, "date": current, "available_count": available_count})
        current += timedelta(days=1)

    stmt = pg_insert(RoomAvailability).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["room_id", "date"],
        set_={"available_count": stmt.excluded.available_count},
    )
    await session.execute(stmt)
    await session.commit()
    return len(rows)


async def list_availability(
    session: AsyncSession,
    *,
    room_id: UUID,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[RoomAvailability]:
    stmt = select(RoomAvailability).where(RoomAvailability.room_id == room_id)
    if from_date is not None:
        stmt = stmt.where(RoomAvailability.date >= from_date)
    if to_date is not None:
        stmt = stmt.where(RoomAvailability.date <= to_date)
    stmt = stmt.order_by(RoomAvailability.date)
    return list((await session.execute(stmt)).scalars().all())

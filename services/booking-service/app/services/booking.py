"""Booking business logic — transactional capacity decrement + publish.

The two-step pattern (commit Postgres FIRST, then publish RabbitMQ) is the
dual-write we mitigate via durable+persistent+retry. If the publish step
fails terminally, the booking still exists (DB is the source of truth) and
the caller learns via `notification_dispatched=false` in the response.
See Plan §3.3.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import structlog
from aio_pika.abc import AbstractRobustConnection
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories import booking as booking_repo
from shared.clients.rabbitmq import publish_with_retry
from shared.models import Booking, User

logger = structlog.get_logger(__name__)


async def create_booking(
    session: AsyncSession,
    *,
    user: User,
    hotel_id: UUID,
    room_id: UUID,
    check_in: date,
    check_out: date,
    guests: int,
    idempotency_key: str | None,
) -> Booking:
    nights = (check_out - check_in).days
    if nights < 1:
        raise HTTPException(status_code=400, detail="check_out must be after check_in")

    # Idempotency: if the client already booked with this key, return that booking.
    if idempotency_key is not None:
        existing = await booking_repo.find_booking_by_idempotency_key(session, idempotency_key)
        if existing is not None:
            return existing

    # Verify the room (and its parent hotel is not soft-deleted) exists.
    row = await booking_repo.get_room_with_hotel(session, room_id)
    if row is None:
        raise HTTPException(status_code=404, detail="room not found")
    room, hotel = row

    if hotel_id != hotel.id:
        raise HTTPException(status_code=400, detail="room does not belong to the supplied hotel_id")
    if guests > room.capacity:
        raise HTTPException(
            status_code=400, detail=f"room capacity {room.capacity} cannot host {guests} guests"
        )

    # Lock the availability rows for the whole stay.
    avail_rows = await booking_repo.lock_availability_range(
        session, room_id=room_id, check_in=check_in, check_out=check_out
    )
    if len(avail_rows) != nights:
        raise HTTPException(
            status_code=409,
            detail=f"availability missing for some dates ({len(avail_rows)}/{nights} present)",
        )
    if any(r.available_count <= 0 for r in avail_rows):
        raise HTTPException(status_code=409, detail="no rooms available for the requested dates")

    # Decrement.
    for r in avail_rows:
        r.available_count -= 1

    # Price: logged-in callers always get the discounted rate (the same one
    # they saw on the search page; see Plan §3.5 + frontend BookingWidget).
    base = room.base_price_per_night
    effective = (base * Decimal(str(settings.discount_rate))).quantize(Decimal("0.01"))
    total = (effective * nights).quantize(Decimal("0.01"))

    booking = Booking(
        user_id=user.id,
        room_id=room_id,
        hotel_id=hotel_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        total_price=total,
        status="confirmed",
        idempotency_key=idempotency_key,
    )
    await booking_repo.insert_booking(session, booking)

    try:
        await session.commit()
    except IntegrityError as exc:
        # Idempotency-Key unique-constraint race: another concurrent request
        # already inserted with the same key. Recover by returning that one.
        await session.rollback()
        if idempotency_key is not None:
            existing = await booking_repo.find_booking_by_idempotency_key(session, idempotency_key)
            if existing is not None:
                logger.info("idempotent_replay", booking_id=str(existing.id))
                return existing
        raise HTTPException(status_code=409, detail="booking conflict") from exc

    await session.refresh(booking)
    # Stash hotel name on the booking object for the caller to publish (not persisted).
    booking._hotel_name = hotel.name  # type: ignore[attr-defined]
    return booking


async def publish_reservation_event(
    connection: AbstractRobustConnection,
    *,
    booking: Booking,
    user: User,
    hotel_name: str,
) -> bool:
    """Durable + persistent publish after the DB commit (see Plan §3.3)."""
    payload = {
        "event_type": "reservation.created",
        "booking_id": str(booking.id),
        "user_email": user.email,
        "user_display_name": user.display_name,
        "hotel_id": str(booking.hotel_id),
        "hotel_name": hotel_name,
        "check_in": booking.check_in.isoformat(),
        "check_out": booking.check_out.isoformat(),
        "guests": booking.guests,
        "total_price": str(booking.total_price),
        "created_at": booking.created_at.replace(tzinfo=timezone.utc).isoformat()
        if booking.created_at.tzinfo is None
        else booking.created_at.isoformat(),
    }
    return await publish_with_retry(
        connection,
        exchange_name=settings.rabbitmq_exchange,
        routing_key=settings.rabbitmq_routing_key,
        payload=payload,
        max_attempts=settings.rabbitmq_publish_max_retries,
    )


async def cancel_booking(session: AsyncSession, *, user: User, booking_id: UUID) -> Booking:
    booking = await booking_repo.get_booking(session, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="not your booking")
    if booking.status != "confirmed":
        raise HTTPException(status_code=409, detail=f"booking is already {booking.status}")

    # Restore availability under the same lock pattern.
    avail_rows = await booking_repo.lock_availability_range(
        session, room_id=booking.room_id, check_in=booking.check_in, check_out=booking.check_out
    )
    for r in avail_rows:
        r.available_count += 1
    booking.status = "cancelled"
    await session.commit()
    await session.refresh(booking)
    return booking

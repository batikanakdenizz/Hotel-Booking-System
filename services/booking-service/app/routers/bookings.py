"""POST/GET/DELETE /api/v1/bookings."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.deps import RabbitMQDep, SessionDep, UserDep
from app.repositories import booking as booking_repo
from app.services import booking as booking_svc
from shared.schemas import (
    BookingCreate,
    BookingResponse,
    BookingStatus,
    PaginatedResponse,
    PaginationParams,
)

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


def _to_response(booking, *, notification_dispatched: bool = True) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        hotel_id=booking.hotel_id,
        room_id=booking.room_id,
        check_in=booking.check_in,
        check_out=booking.check_out,
        guests=booking.guests,
        total_price=booking.total_price,
        status=BookingStatus(booking.status),
        created_at=booking.created_at,
        notification_dispatched=notification_dispatched,
    )


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking_endpoint(
    payload: BookingCreate,
    user: UserDep,
    session: SessionDep,
    rabbitmq: RabbitMQDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> BookingResponse:
    booking = await booking_svc.create_booking(
        session,
        user=user,
        hotel_id=payload.hotel_id,
        room_id=payload.room_id,
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        idempotency_key=idempotency_key,
    )
    # Publish AFTER DB commit (Plan §3.3 ordering).
    hotel_name = getattr(booking, "_hotel_name", "")
    notification_ok = await booking_svc.publish_reservation_event(
        rabbitmq, booking=booking, user=user, hotel_name=hotel_name
    )
    return _to_response(booking, notification_dispatched=notification_ok)


@router.get("", response_model=PaginatedResponse[BookingResponse])
async def list_my_bookings(
    user: UserDep,
    session: SessionDep,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[BookingResponse]:
    items, total = await booking_repo.list_user_bookings(
        session, user_id=user.id, offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse[BookingResponse](
        items=[_to_response(b) for b in items],
        page=pagination.page,
        limit=pagination.limit,
        total=total,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_endpoint(
    booking_id: UUID, user: UserDep, session: SessionDep
) -> BookingResponse:
    booking = await booking_repo.get_booking(session, booking_id)
    if booking is None or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="booking not found")
    return _to_response(booking)


@router.delete("/{booking_id}", response_model=BookingResponse)
async def cancel_booking_endpoint(
    booking_id: UUID, user: UserDep, session: SessionDep
) -> BookingResponse:
    booking = await booking_svc.cancel_booking(session, user=user, booking_id=booking_id)
    return _to_response(booking)

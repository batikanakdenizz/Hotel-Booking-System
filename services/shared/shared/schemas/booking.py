"""Booking DTOs + the RabbitMQ event envelope."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BookingStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingCreate(BaseModel):
    """POST /api/v1/bookings body."""

    hotel_id: UUID
    room_id: UUID
    check_in: date
    check_out: date
    guests: int = Field(ge=1, le=10)


class BookingResponse(BaseModel):
    """Booking detail (own bookings list + booking creation 201 body)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    hotel_id: UUID
    room_id: UUID
    check_in: date
    check_out: date
    guests: int
    total_price: Decimal
    status: BookingStatus
    created_at: datetime
    notification_dispatched: bool = Field(
        default=True,
        description="False if the durable+retry publish exhausted attempts (see Plan §3.3 dual-write note)",
    )


class ReservationCreatedEvent(BaseModel):
    """Body of the RabbitMQ message booking-service publishes after a successful booking.

    Notification-service consumes this and turns it into a confirmation email.
    Schema mirrors Plan §5.4 — keep this and the RabbitMQ payload in lockstep.
    """

    event_type: str = Field(default="reservation.created")
    booking_id: UUID
    user_email: EmailStr
    user_display_name: str | None = None
    hotel_id: UUID
    hotel_name: str
    check_in: date
    check_out: date
    guests: int
    total_price: Decimal
    created_at: datetime

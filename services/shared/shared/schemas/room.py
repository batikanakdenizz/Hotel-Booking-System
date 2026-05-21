"""Room + RoomAvailability DTOs."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomBase(BaseModel):
    """Room type definition under a hotel (multiple rooms of this type may exist)."""

    room_type: str = Field(min_length=1, max_length=100, description="'Single' | 'Double' | 'Suite' etc.")
    capacity: int = Field(ge=1, le=10, description="Max guests per room")
    base_price_per_night: Decimal = Field(ge=Decimal("0"), decimal_places=2)
    total_rooms: int = Field(ge=1, description="How many physical rooms of this type the hotel has")


class RoomCreate(RoomBase):
    """POST /api/v1/admin/hotels/{hotel_id}/rooms body."""

    pass


class RoomUpdate(BaseModel):
    """PATCH /api/v1/admin/rooms/{room_id} body — all optional."""

    room_type: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int | None = Field(default=None, ge=1, le=10)
    base_price_per_night: Decimal | None = Field(default=None, ge=Decimal("0"), decimal_places=2)
    total_rooms: int | None = Field(default=None, ge=1)


class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hotel_id: UUID
    created_at: datetime


class RoomAvailabilityUpdate(BaseModel):
    """PUT /api/v1/admin/rooms/{room_id}/availability body.

    Inclusive range. The service expands this into one row per day.
    """

    start_date: date
    end_date: date
    available_count: int = Field(ge=0, description="Number of this room type free on each day in range")


class RoomAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    date: date
    available_count: int

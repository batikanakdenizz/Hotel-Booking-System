"""Pydantic v2 schemas shared across services.

Each entity module exposes three layers:
  - {Entity}Base    — fields common to create + read
  - {Entity}Create  — payload accepted by POST endpoints
  - {Entity}Update  — payload accepted by PUT/PATCH (all optional)
  - {Entity}Response — what the API returns (adds id, created_at, etc.)

Generic helpers live in `common.py` (pagination envelope, error shape).
"""
from shared.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
)
from shared.schemas.user import UserBase, UserCreate, UserResponse, UserRole
from shared.schemas.hotel import HotelBase, HotelCreate, HotelResponse, HotelUpdate
from shared.schemas.room import (
    RoomAvailabilityResponse,
    RoomAvailabilityUpdate,
    RoomBase,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from shared.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingStatus,
    ReservationCreatedEvent,
)
from shared.schemas.comment import (
    CommentCreate,
    CommentResponse,
    RatingDistribution,
    Ratings,
)

__all__ = [
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationParams",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserRole",
    "HotelBase",
    "HotelCreate",
    "HotelResponse",
    "HotelUpdate",
    "RoomBase",
    "RoomCreate",
    "RoomResponse",
    "RoomUpdate",
    "RoomAvailabilityResponse",
    "RoomAvailabilityUpdate",
    "BookingCreate",
    "BookingResponse",
    "BookingStatus",
    "ReservationCreatedEvent",
    "CommentCreate",
    "CommentResponse",
    "Ratings",
    "RatingDistribution",
]

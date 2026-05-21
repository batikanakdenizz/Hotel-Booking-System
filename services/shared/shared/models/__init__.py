"""SQLAlchemy 2.0 declarative ORM models — single source of truth for the Postgres schema.

Imported by:
  - Every service that needs to query (admin, search, booking, notification)
  - admin-service/migrations/env.py (Alembic — schema owner)

Note we deviate from Plan §7 here (which placed models under admin-service/app/models/).
Putting them under shared/ avoids cross-service imports: every service depends on
shared/, not on other services. Admin-service is still the schema OWNER — Alembic
migrations live there.
"""
from shared.models.base import Base
from shared.models.booking import Booking
from shared.models.hotel import Hotel
from shared.models.room import Room
from shared.models.room_availability import RoomAvailability
from shared.models.user import User

__all__ = [
    "Base",
    "User",
    "Hotel",
    "Room",
    "RoomAvailability",
    "Booking",
]

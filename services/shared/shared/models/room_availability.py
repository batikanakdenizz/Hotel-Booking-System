"""room_availability — one row per (room_id, date). Plan §5.1.

This table is the canonical source for "how many rooms of this type are free
on date X". Booking-service decrements available_count under SELECT FOR UPDATE
inside a transaction (see Plan §3.3).

NOT cached — search-service joins this table fresh on every query (Plan §3.5).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, uuid_fk, uuid_pk


class RoomAvailability(Base):
    __tablename__ = "room_availability"

    id: Mapped[uuid_pk]
    room_id: Mapped[uuid_fk] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    # Number of physical rooms of this type free on this date.
    # Decremented to 0 (not negative) — booking-service asserts > 0 before decrement.
    available_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    __table_args__ = (
        # One row per (room, date). Idempotent upserts use ON CONFLICT.
        UniqueConstraint("room_id", "date", name="uq_room_availability_room_date"),
        Index("idx_room_availability_date", "room_id", "date"),
    )

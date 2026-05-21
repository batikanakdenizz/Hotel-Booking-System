"""bookings table — Plan §5.1.

Created by booking-service inside the same transaction that decrements
room_availability. After the COMMIT, booking-service publishes a
`reservation.created` event to RabbitMQ (durable + persistent + retry,
see Plan §3.3).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, created_at, money, uuid_fk, uuid_pk


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid_pk]
    user_id: Mapped[uuid_fk] = mapped_column(ForeignKey("users.id"), nullable=False)
    room_id: Mapped[uuid_fk] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    hotel_id: Mapped[uuid_fk] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    guests: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_price: Mapped[money]
    # 'confirmed' | 'cancelled'
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="confirmed")
    # Optional client-supplied key for idempotency (booking-service uses unique index)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[created_at]

    __table_args__ = (
        Index("idx_bookings_user_id", "user_id"),
        Index("idx_bookings_dates", "check_in", "check_out"),
    )

"""rooms table — Plan §5.1."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, created_at, money, uuid_fk, uuid_pk


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid_pk]
    hotel_id: Mapped[uuid_fk] = mapped_column(ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    # "Single", "Double", "Suite" etc.
    room_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Max guests per physical room of this type.
    capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    base_price_per_night: Mapped[money]
    # How many physical rooms of this type the hotel has.
    # Decremented from room_availability.available_count, not from this column.
    total_rooms: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[created_at]

    __table_args__ = (
        Index("idx_rooms_hotel_id", "hotel_id"),
    )

"""hotels table — schema mirrors Plan §5.1."""
from __future__ import annotations

from sqlalchemy import Float, Index, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, created_at, deleted_at, updated_at, uuid_pk


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[uuid_pk]
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Searchable city/region — admin-service lowercases on write.
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    # Recipient for nightly low-capacity alerts.
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    star_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    amenities: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    deleted_at: Mapped[deleted_at]

    __table_args__ = (
        # Functional index — search-service hits LOWER(destination) on every query.
        Index("idx_hotels_destination", func.lower(destination)),
        # Helps the radius-search bonus feature if we add it later.
        Index("idx_hotels_location", "latitude", "longitude"),
    )

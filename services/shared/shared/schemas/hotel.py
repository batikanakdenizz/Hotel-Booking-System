"""Hotel DTOs — matches Plan §5.1 hotels table."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class HotelBase(BaseModel):
    """Common fields that an admin can set on a hotel."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    destination: str = Field(
        min_length=1,
        max_length=255,
        description="Searchable city/region (e.g. 'Rome', 'Istanbul'). Lowercased server-side.",
    )
    address: str = Field(min_length=1)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    admin_email: EmailStr = Field(description="Recipient of low-capacity alerts (nightly task)")
    star_rating: int | None = Field(default=None, ge=1, le=5)
    amenities: list[str] = Field(default_factory=list, description="e.g. ['wifi', 'pool', 'breakfast']")
    image_url: str | None = None


class HotelCreate(HotelBase):
    """POST /api/v1/admin/hotels body."""

    pass


class HotelUpdate(BaseModel):
    """PATCH-style update — every field optional.

    We do NOT subclass HotelBase here because we want every field optional;
    Pydantic v2 doesn't have a clean built-in `Optional[ALL]` so we redefine.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    destination: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    admin_email: EmailStr | None = None
    star_rating: int | None = Field(default=None, ge=1, le=5)
    amenities: list[str] | None = None
    image_url: str | None = None


class HotelResponse(HotelBase):
    """Hotel detail in API responses (admin + public search)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

"""Response DTOs specific to search-service.

The shape matches Plan §6.3 — every available room of a hotel is included as
a row under `available_rooms`, with both the original and the post-discount
price so the frontend can render the strikethrough UI naturally.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AvailableRoom(BaseModel):
    """One bookable room type within a hotel for the requested date range."""

    model_config = ConfigDict(from_attributes=False)

    room_id: UUID
    room_type: str
    capacity: int
    # Lowest available count across the date range (>= 1 by construction).
    available_count: int
    # Pricing — original is the base, price_per_night is what user pays
    # (discounted if logged in, equal to original otherwise).
    original_price: Decimal
    price_per_night: Decimal
    discount_applied: bool


class SearchResultItem(BaseModel):
    """One hotel in the search results list."""

    hotel_id: UUID
    name: str
    description: str | None
    destination: str
    address: str
    latitude: float
    longitude: float
    star_rating: int | None
    amenities: list[str]
    image_url: str | None
    available_rooms: list[AvailableRoom]


class HotelDetailResponse(SearchResultItem):
    """Same shape as a search result item — single hotel detail endpoint reuses it."""

    pass

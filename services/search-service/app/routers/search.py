"""GET /api/v1/search + GET /api/v1/search/hotels/{hotel_id}.

Both reuse the same merge logic: availability fresh from Postgres, static
hotel detail from Redis (cache-aside), discount applied at response-build
time (never persisted in cache). See Plan §3.5.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import settings
from app.deps import OptionalUserDep, RedisDep, SessionDep
from app.schemas import AvailableRoom, HotelDetailResponse, SearchResultItem
from app.services import availability as avail_svc
from app.services import cache as cache_svc
from app.services import pricing as pricing_svc
from shared.schemas import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/api/v1/search", tags=["search"])


def _build_result_item(
    hotel_payload: dict,
    available_rows: list[avail_svc.AvailableRoomRow],
    *,
    is_authenticated: bool,
) -> SearchResultItem:
    """Merge cached static info with fresh availability, apply discount."""
    # Map room_id -> base_price_per_night from the cached payload.
    base_price_by_room = {
        r["id"]: cache_svc.to_decimal(r["base_price_per_night"])
        for r in hotel_payload["rooms"]
    }

    available_rooms: list[AvailableRoom] = []
    for row in available_rows:
        room_id_str = str(row.room_id)
        base = base_price_by_room.get(room_id_str)
        if base is None:
            # Room exists in availability but not in cached hotel detail —
            # extremely rare race (admin just added a room, cache not yet
            # invalidated). Skip rather than return broken pricing.
            continue
        effective, discount_applied = pricing_svc.apply_discount(
            base, is_authenticated=is_authenticated, discount_rate=settings.discount_rate
        )
        available_rooms.append(
            AvailableRoom(
                room_id=row.room_id,
                room_type=row.room_type,
                capacity=row.capacity,
                available_count=row.min_available,
                original_price=base,
                price_per_night=effective,
                discount_applied=discount_applied,
            )
        )

    return SearchResultItem(
        hotel_id=UUID(hotel_payload["id"]),
        name=hotel_payload["name"],
        description=hotel_payload.get("description"),
        destination=hotel_payload["destination"],
        address=hotel_payload["address"],
        latitude=hotel_payload["latitude"],
        longitude=hotel_payload["longitude"],
        star_rating=hotel_payload.get("star_rating"),
        amenities=hotel_payload.get("amenities", []),
        image_url=hotel_payload.get("image_url"),
        available_rooms=available_rooms,
    )


@router.get("", response_model=PaginatedResponse[SearchResultItem])
async def search_hotels(
    session: SessionDep,
    redis: RedisDep,
    user: OptionalUserDep,
    destination: str = Query(min_length=1),
    check_in: date = Query(),
    check_out: date = Query(),
    guests: int = Query(ge=1, le=10),
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[SearchResultItem]:
    is_authenticated = user is not None
    destination_lower = destination.strip().lower()

    # 1. Destination -> hotel_ids (cached, 6h TTL).
    hotel_id_strings = await cache_svc.get_destination_hotel_ids(
        redis, session, destination_lower, ttl_seconds=settings.destination_index_ttl_seconds
    )
    if not hotel_id_strings:
        return PaginatedResponse[SearchResultItem](items=[], page=pagination.page, limit=pagination.limit, total=0)

    hotel_ids = [UUID(s) for s in hotel_id_strings]

    # 2. Fresh availability query (never cached).
    available_rows = await avail_svc.query_available_rooms(
        session, hotel_ids=hotel_ids, check_in=check_in, check_out=check_out, guests=guests
    )

    # 3. Bucket by hotel_id and only keep hotels with at least one available room.
    rows_by_hotel: dict[UUID, list[avail_svc.AvailableRoomRow]] = {}
    for row in available_rows:
        rows_by_hotel.setdefault(row.hotel_id, []).append(row)

    matched_hotel_ids = list(rows_by_hotel.keys())
    total = len(matched_hotel_ids)

    # 4. Paginate at the hotel level.
    paged_ids = matched_hotel_ids[pagination.offset : pagination.offset + pagination.limit]

    # 5. Hydrate static hotel detail + apply discount.
    items: list[SearchResultItem] = []
    for hid in paged_ids:
        payload = await cache_svc.get_hotel_detail(
            redis, session, hid, ttl_seconds=settings.hotel_detail_ttl_seconds
        )
        if payload is None:
            continue  # hotel was soft-deleted between availability query and this read
        items.append(_build_result_item(payload, rows_by_hotel[hid], is_authenticated=is_authenticated))

    return PaginatedResponse[SearchResultItem](
        items=items,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
    )


@router.get("/hotels/{hotel_id}", response_model=HotelDetailResponse)
async def get_hotel_detail_endpoint(
    hotel_id: UUID,
    session: SessionDep,
    redis: RedisDep,
    user: OptionalUserDep,
    check_in: date | None = Query(default=None),
    check_out: date | None = Query(default=None),
    guests: int = Query(default=1, ge=1, le=10),
) -> HotelDetailResponse:
    """Hotel detail endpoint — used by the detail page.

    If check_in + check_out are supplied, available_rooms is computed against
    them; otherwise it falls back to the next 7 days so the UI still has rooms
    to display before the user picks dates.
    """
    payload = await cache_svc.get_hotel_detail(
        redis, session, hotel_id, ttl_seconds=settings.hotel_detail_ttl_seconds
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="hotel not found")

    today = date.today()
    if check_in is None or check_out is None:
        from datetime import timedelta
        check_in = today
        check_out = today + timedelta(days=7)

    rows = await avail_svc.query_available_rooms(
        session, hotel_ids=[hotel_id], check_in=check_in, check_out=check_out, guests=guests
    )

    result = _build_result_item(payload, rows, is_authenticated=user is not None)
    return HotelDetailResponse(**result.model_dump())

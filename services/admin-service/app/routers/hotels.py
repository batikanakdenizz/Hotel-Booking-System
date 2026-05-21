"""POST/GET/PUT/DELETE /api/v1/admin/hotels."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.cache import invalidate_destination, invalidate_hotel
from app.deps import AdminDep, RedisDep, SessionDep
from app.repositories import hotel as hotel_repo
from shared.schemas import HotelCreate, HotelResponse, HotelUpdate, PaginatedResponse, PaginationParams

router = APIRouter(prefix="/api/v1/admin/hotels", tags=["admin-hotels"])


@router.post("", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel_endpoint(
    payload: HotelCreate,
    admin: AdminDep,
    session: SessionDep,
    redis: RedisDep,
) -> HotelResponse:
    data = payload.model_dump()
    # Normalize destination for search-service's lowercase index match.
    data["destination"] = data["destination"].strip()
    hotel = await hotel_repo.create_hotel(session, data=data)
    # New hotel in this destination → drop the cached id list.
    await invalidate_destination(redis, hotel.destination.lower())
    return HotelResponse.model_validate(hotel)


@router.get("", response_model=PaginatedResponse[HotelResponse])
async def list_hotels_endpoint(
    admin: AdminDep,
    session: SessionDep,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[HotelResponse]:
    items, total = await hotel_repo.list_hotels(session, offset=pagination.offset, limit=pagination.limit)
    return PaginatedResponse[HotelResponse](
        items=[HotelResponse.model_validate(i) for i in items],
        page=pagination.page,
        limit=pagination.limit,
        total=total,
    )


@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel_endpoint(hotel_id: UUID, admin: AdminDep, session: SessionDep) -> HotelResponse:
    hotel = await hotel_repo.get_hotel(session, hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    return HotelResponse.model_validate(hotel)


@router.put("/{hotel_id}", response_model=HotelResponse)
async def update_hotel_endpoint(
    hotel_id: UUID,
    payload: HotelUpdate,
    admin: AdminDep,
    session: SessionDep,
    redis: RedisDep,
) -> HotelResponse:
    hotel = await hotel_repo.get_hotel(session, hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="hotel not found")

    old_destination = hotel.destination.lower()
    updated = await hotel_repo.update_hotel(
        session, hotel, changes=payload.model_dump(exclude_unset=True)
    )

    # Always invalidate the hotel detail.
    await invalidate_hotel(redis, str(updated.id))
    # If destination changed, both old + new destination lists are stale.
    new_destination = updated.destination.lower()
    await invalidate_destination(redis, new_destination)
    if new_destination != old_destination:
        await invalidate_destination(redis, old_destination)

    return HotelResponse.model_validate(updated)


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_hotel_endpoint(
    hotel_id: UUID,
    admin: AdminDep,
    session: SessionDep,
    redis: RedisDep,
) -> None:
    hotel = await hotel_repo.get_hotel(session, hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    destination_lower = hotel.destination.lower()
    await hotel_repo.soft_delete_hotel(session, hotel)
    await invalidate_hotel(redis, str(hotel.id))
    await invalidate_destination(redis, destination_lower)

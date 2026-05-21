"""POST/GET /api/v1/admin/hotels/{hid}/rooms; PUT/GET availability."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.cache import invalidate_hotel
from app.deps import AdminDep, RedisDep, SessionDep
from app.repositories import hotel as hotel_repo
from shared.schemas import (
    PaginatedResponse,
    PaginationParams,
    RoomAvailabilityResponse,
    RoomAvailabilityUpdate,
    RoomCreate,
    RoomResponse,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin-rooms"])


@router.post(
    "/hotels/{hotel_id}/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_endpoint(
    hotel_id: UUID,
    payload: RoomCreate,
    admin: AdminDep,
    session: SessionDep,
    redis: RedisDep,
) -> RoomResponse:
    hotel = await hotel_repo.get_hotel(session, hotel_id)
    if hotel is None:
        raise HTTPException(status_code=404, detail="hotel not found")
    room = await hotel_repo.create_room(session, hotel_id=hotel_id, data=payload.model_dump())
    # base_prices are part of the cached hotel:{id} payload (per Plan §3.5),
    # so any room mutation invalidates the parent hotel cache entry.
    await invalidate_hotel(redis, str(hotel_id))
    return RoomResponse.model_validate(room)


@router.get(
    "/hotels/{hotel_id}/rooms",
    response_model=PaginatedResponse[RoomResponse],
)
async def list_rooms_endpoint(
    hotel_id: UUID,
    admin: AdminDep,
    session: SessionDep,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[RoomResponse]:
    items, total = await hotel_repo.list_rooms(
        session, hotel_id=hotel_id, offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse[RoomResponse](
        items=[RoomResponse.model_validate(i) for i in items],
        page=pagination.page,
        limit=pagination.limit,
        total=total,
    )


@router.put("/rooms/{room_id}/availability", status_code=status.HTTP_200_OK)
async def upsert_availability_endpoint(
    room_id: UUID,
    payload: RoomAvailabilityUpdate,
    admin: AdminDep,
    session: SessionDep,
) -> dict[str, int | str]:
    """Bulk upsert availability for every day in [start_date, end_date]."""
    room = await hotel_repo.get_room(session, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="room not found")
    days = await hotel_repo.upsert_availability_range(
        session,
        room_id=room_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        available_count=payload.available_count,
    )
    return {"room_id": str(room_id), "days_upserted": days}


@router.get(
    "/rooms/{room_id}/availability",
    response_model=list[RoomAvailabilityResponse],
)
async def list_availability_endpoint(
    room_id: UUID,
    admin: AdminDep,
    session: SessionDep,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> list[RoomAvailabilityResponse]:
    rows = await hotel_repo.list_availability(session, room_id=room_id, from_date=from_date, to_date=to_date)
    return [RoomAvailabilityResponse.model_validate(r) for r in rows]

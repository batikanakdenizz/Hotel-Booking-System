"""POST/GET/DELETE comments + GET distribution.

Auth policy (Plan §4.1):
  - POST /api/v1/comments              auth required
  - GET  /api/v1/comments/hotels/{id}  public
  - GET  /api/v1/comments/hotels/{id}/distribution   public
  - DELETE /api/v1/comments/{id}       auth required (must own)
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.deps import ClaimsDep, CollectionDep
from app.repositories import comment as comment_repo
from shared.schemas import (
    CommentCreate,
    CommentResponse,
    PaginatedResponse,
    PaginationParams,
    Ratings,
    RatingDistribution,
)

router = APIRouter(prefix="/api/v1/comments", tags=["comments"])


def _doc_to_response(doc: dict) -> CommentResponse:
    return CommentResponse.model_validate(
        {
            "_id": str(doc["_id"]),
            "hotel_id": doc["hotel_id"],
            "user_id": doc["user_id"],
            "user_display_name": doc.get("user_display_name"),
            "text": doc["text"],
            "ratings": doc["ratings"],
            "overall_rating": doc["overall_rating"],
            "created_at": doc["created_at"],
        }
    )


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment_endpoint(
    payload: CommentCreate,
    claims: ClaimsDep,
    collection: CollectionDep,
) -> CommentResponse:
    ratings = payload.ratings
    overall = ratings.average  # mean of the 5 dimensions, 1-decimal precision
    doc = {
        "hotel_id": payload.hotel_id,
        "user_id": claims["uid"],
        "user_display_name": claims.get("name"),
        "text": payload.text,
        "ratings": ratings.model_dump(),
        "overall_rating": overall,
        "created_at": datetime.now(timezone.utc),
        "deleted_at": None,
    }
    new_id = await comment_repo.insert_one(collection, doc)
    doc["_id"] = new_id
    return _doc_to_response(doc)


@router.get(
    "/hotels/{hotel_id}",
    response_model=PaginatedResponse[CommentResponse],
)
async def list_comments_endpoint(
    hotel_id: str,
    collection: CollectionDep,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[CommentResponse]:
    items, total = await comment_repo.list_for_hotel(
        collection, hotel_id=hotel_id, skip=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse[CommentResponse](
        items=[_doc_to_response(d) for d in items],
        page=pagination.page,
        limit=pagination.limit,
        total=total,
    )


@router.get(
    "/hotels/{hotel_id}/distribution",
    response_model=RatingDistribution,
)
async def get_distribution_endpoint(
    hotel_id: str, collection: CollectionDep
) -> RatingDistribution:
    """Feeds the per-service bar chart + overall histogram on the hotel detail page."""
    data = await comment_repo.aggregate_distribution(collection, hotel_id=hotel_id)
    avg = data["averages"]
    return RatingDistribution(
        total_comments=avg["total_comments"],
        avg_cleanliness=avg.get("avg_cleanliness"),
        avg_staff=avg.get("avg_staff"),
        avg_amenities=avg.get("avg_amenities"),
        avg_comfort=avg.get("avg_comfort"),
        avg_eco_friendliness=avg.get("avg_eco_friendliness"),
        avg_overall=avg.get("avg_overall"),
        breakdown=data["breakdown"],
    )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_comment_endpoint(
    claims: ClaimsDep,
    collection: CollectionDep,
    comment_id: str = Path(min_length=1),
) -> None:
    doc = await comment_repo.get_one(collection, comment_id)
    if doc is None or doc.get("deleted_at") is not None:
        raise HTTPException(status_code=404, detail="comment not found")
    if doc["user_id"] != claims["uid"]:
        raise HTTPException(status_code=403, detail="not your comment")
    ok = await comment_repo.soft_delete(collection, comment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="comment not found")

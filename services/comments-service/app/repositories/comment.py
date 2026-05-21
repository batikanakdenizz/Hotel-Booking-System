"""Pure Motor calls. No HTTP, no business rules."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection


async def insert_one(collection: AsyncIOMotorCollection, doc: dict) -> str:
    result = await collection.insert_one(doc)
    return str(result.inserted_id)


async def list_for_hotel(
    collection: AsyncIOMotorCollection,
    *,
    hotel_id: str,
    skip: int,
    limit: int,
) -> tuple[list[dict], int]:
    """Return (docs, total) for the public listing endpoint.

    Sorted newest-first. Excludes soft-deleted rows.
    """
    query = {"hotel_id": hotel_id, "deleted_at": None}
    total = await collection.count_documents(query)
    cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = [doc async for doc in cursor]
    return items, total


async def get_one(collection: AsyncIOMotorCollection, comment_id: str) -> dict | None:
    if not ObjectId.is_valid(comment_id):
        return None
    return await collection.find_one({"_id": ObjectId(comment_id)})


async def soft_delete(collection: AsyncIOMotorCollection, comment_id: str) -> bool:
    if not ObjectId.is_valid(comment_id):
        return False
    result = await collection.update_one(
        {"_id": ObjectId(comment_id), "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}},
    )
    return result.modified_count == 1


async def aggregate_distribution(
    collection: AsyncIOMotorCollection, *, hotel_id: str
) -> dict[str, Any]:
    """Per Plan §5.3 — 5 dimension averages + score-distribution histogram.

    Two parallel aggregations:
      1. $group → total + 5 averages (single doc, fast)
      2. $bucket on overall_rating → counts per integer bucket 1..10
    """
    match_stage = {"$match": {"hotel_id": hotel_id, "deleted_at": None}}

    averages_pipeline = [
        match_stage,
        {
            "$group": {
                "_id": None,
                "total_comments": {"$sum": 1},
                "avg_cleanliness": {"$avg": "$ratings.cleanliness"},
                "avg_staff": {"$avg": "$ratings.staff"},
                "avg_amenities": {"$avg": "$ratings.amenities"},
                "avg_comfort": {"$avg": "$ratings.comfort"},
                "avg_eco_friendliness": {"$avg": "$ratings.eco_friendliness"},
                "avg_overall": {"$avg": "$overall_rating"},
            }
        },
    ]
    breakdown_pipeline = [
        match_stage,
        {
            "$bucket": {
                "groupBy": "$overall_rating",
                "boundaries": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                "default": "other",
                "output": {"count": {"$sum": 1}},
            }
        },
    ]

    averages_docs = [d async for d in collection.aggregate(averages_pipeline)]
    breakdown_docs = [d async for d in collection.aggregate(breakdown_pipeline)]

    averages = averages_docs[0] if averages_docs else {
        "total_comments": 0,
        "avg_cleanliness": None,
        "avg_staff": None,
        "avg_amenities": None,
        "avg_comfort": None,
        "avg_eco_friendliness": None,
        "avg_overall": None,
    }
    breakdown: dict[int, int] = {}
    for row in breakdown_docs:
        key = row["_id"]
        if isinstance(key, int):
            breakdown[key] = int(row["count"])
    return {"averages": averages, "breakdown": breakdown}

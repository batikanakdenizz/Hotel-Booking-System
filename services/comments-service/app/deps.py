"""Dependencies — Mongo db handle + optional/required auth.

comments-service identifies users by Firebase UID (string), so we do NOT need
the Postgres get_or_create_user dep here. Just verify the token and read
claims["uid"]. Reads (GET) are public; writes (POST/DELETE) require auth.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from shared.auth.deps import FirebaseClaims, get_current_user, optional_current_user


async def get_mongo_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.mongo_db


async def get_comments_collection(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
) -> AsyncIOMotorCollection:
    return db["comments"]


CollectionDep = Annotated[AsyncIOMotorCollection, Depends(get_comments_collection)]
ClaimsDep = Annotated[FirebaseClaims, Depends(get_current_user)]
OptionalClaimsDep = Annotated[FirebaseClaims | None, Depends(optional_current_user)]

"""User DTOs.

Identity comes from Firebase (the `firebase_uid` field). Our Postgres `users`
row is created lazily on the first authenticated request — see Plan §3.2.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(StrEnum):
    """Source of truth for who can hit /api/v1/admin/*.

    Stored as a string column in Postgres (see shared.models.user).
    Promotion is out-of-band via scripts/promote_admin.py — there's
    no public endpoint that flips this.
    """

    USER = "user"
    HOTEL_ADMIN = "hotel_admin"


class UserBase(BaseModel):
    """Fields a caller is allowed to send when shaping a user row."""

    email: EmailStr
    display_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    """Internal-use only — populated by the get_or_create_user dep."""

    firebase_uid: str = Field(min_length=1, max_length=128)


class UserResponse(UserBase):
    """What we return from /me-style endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    firebase_uid: str
    role: UserRole
    created_at: datetime

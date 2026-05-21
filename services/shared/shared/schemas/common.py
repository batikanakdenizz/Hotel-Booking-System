"""Common DTOs reused across every API: pagination envelope, error shape."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query-string params for any paginated list endpoint.

    Used via FastAPI's `Depends(PaginationParams)` — every list route gets
    `?page=&limit=` for free, with the same bounds applied uniformly.
    """

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    limit: int = Field(default=20, ge=1, le=100, description="page size (max 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard envelope for every list endpoint.

    Lets the frontend render `Showing X-Y of Z` without doing client-side math.
    """

    items: list[T]
    page: int
    limit: int
    total: int


class ErrorResponse(BaseModel):
    """Uniform error body. FastAPI emits this from our custom exception handlers.

    `code` is a machine-readable identifier the frontend can switch on
    (e.g. show a specific toast). `detail` is human-readable.
    """

    detail: str
    code: str = Field(default="error")

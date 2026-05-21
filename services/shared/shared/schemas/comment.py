"""Comment DTOs — MongoDB-backed, mirrors the PDF mockup's 5 service dimensions.

See Plan §5.2 + §5.3. Ratings use a 1-10 scale to match the Booking.com-style
mockup in Final_Guideline.pdf.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Ratings(BaseModel):
    """The 5 service dimensions shown in the PDF mockup.

    Turkish labels (for reference): Temizlik / Personel ve servis /
    İmkân ve özellikler / Konaklama yerinin durumu / Çevre dostluğu.
    """

    cleanliness: int = Field(ge=1, le=10)
    staff: int = Field(ge=1, le=10)
    amenities: int = Field(ge=1, le=10)
    comfort: int = Field(ge=1, le=10)
    eco_friendliness: int = Field(ge=1, le=10)

    @property
    def average(self) -> float:
        """Mean of the 5 dimensions; written to MongoDB as overall_rating."""
        return round(
            (self.cleanliness + self.staff + self.amenities + self.comfort + self.eco_friendliness) / 5,
            2,
        )


class CommentCreate(BaseModel):
    """POST /api/v1/comments body."""

    hotel_id: str = Field(description="UUID string from Postgres hotels.id")
    text: str = Field(min_length=1, max_length=5000)
    ratings: Ratings


class CommentResponse(BaseModel):
    """Single comment object in the listing endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", description="Mongo ObjectId hex string")
    hotel_id: str
    user_id: str = Field(description="Firebase UID of the author")
    user_display_name: str | None = None
    text: str
    ratings: Ratings
    overall_rating: float
    created_at: datetime


class RatingDistribution(BaseModel):
    """Output of /api/v1/comments/hotels/{hotel_id}/distribution.

    The 5 averages feed the horizontal bar chart on the hotel detail page;
    `breakdown` (counts by overall score bucket 1-10) feeds the histogram.
    See Plan §5.3 aggregation pipeline.
    """

    total_comments: int
    avg_cleanliness: float | None
    avg_staff: float | None
    avg_amenities: float | None
    avg_comfort: float | None
    avg_eco_friendliness: float | None
    avg_overall: float | None
    breakdown: dict[int, int] = Field(
        default_factory=dict,
        description="Map of floor(overall_rating) -> count; keys 1..10",
    )

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.schemas.book import BookSummary


class ReviewCreate(BaseModel):
    book_id: UUID
    rating: int  # 1-5
    review_text: str | None = None


class ReviewResponse(BaseModel):
    id: UUID
    user_name: str
    user_initial: str
    rating: int
    review_text: str | None = None
    created_at: str


class MyReviewResponse(BaseModel):
    id: UUID
    book: BookSummary
    rating: int
    review_text: str | None = None
    created_at: str


class BookReviewsResponse(BaseModel):
    reviews: list[ReviewResponse]
    avg_rating: float
    rating_count: int
    rating_distribution: dict
    total: int
    page: int
    limit: int

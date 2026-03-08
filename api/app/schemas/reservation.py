from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.schemas.book import BookSummary


class ReserveRequest(BaseModel):
    book_id: UUID


class ReservationResponse(BaseModel):
    id: UUID
    book: BookSummary
    status: str
    queue_position: int | None = None
    expires_at: str | None = None
    reserved_at: str


class ReservationsListResponse(BaseModel):
    reservations: list[ReservationResponse]

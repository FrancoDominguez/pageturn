from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str
    max_loans: int
    active_loan_count: int = 0
    outstanding_fines: float = 0.0
    created_at: str


class ReadingProfileResponse(BaseModel):
    total_books_read: int
    favorite_genres: list[dict]
    favorite_authors: list[dict]
    avg_rating_given: float | None = None
    recent_reads: list[dict]
    highly_rated: list[dict]


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str
    active_loans: int = 0
    outstanding_fines: float = 0.0
    created_at: str


class AdminUsersListResponse(BaseModel):
    users: list[AdminUserResponse]
    total: int
    page: int


class AdminUserDetailResponse(BaseModel):
    user: dict
    active_loans: list = []
    loan_history: list = []
    reservations: list = []
    fines: list = []
    reviews: list = []


class UserUpdate(BaseModel):
    max_loans: int | None = None
    role: str | None = None


class PromoteRequest(BaseModel):
    role: str  # "admin" or "user"


class StatsResponse(BaseModel):
    total_books: int
    total_copies: int
    active_loans: int
    overdue_loans: int
    total_users: int
    total_fines_outstanding: float
    loans_today: int = 0
    returns_today: int = 0

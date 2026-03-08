from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class FineResponse(BaseModel):
    id: UUID
    book_title: str
    book_author: str
    book_cover_url: str | None = None
    loan_id: UUID
    amount: float
    daily_rate: float | None = None
    days_overdue: int | None = None
    reason: str
    status: str
    created_at: str


class FinesListResponse(BaseModel):
    fines: list[FineResponse]
    total_outstanding: float
    checkout_blocked: bool


class AdminFineResponse(BaseModel):
    id: UUID
    user: dict
    book_title: str
    amount: float
    reason: str
    status: str
    created_at: str


class AdminFinesListResponse(BaseModel):
    fines: list[AdminFineResponse]
    total: int
    total_outstanding_amount: float

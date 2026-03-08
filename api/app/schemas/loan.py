from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.schemas.book import BookSummary


class CheckoutRequest(BaseModel):
    book_id: UUID


class LoanResponse(BaseModel):
    id: UUID
    book: BookSummary
    checked_out_at: str
    due_date: str
    returned_at: str | None = None
    days_remaining: int
    renewed_count: int
    can_renew: bool
    renewal_blocked_reason: str | None = None
    status: str
    accrued_fine: float | None = None
    daily_rate: float | None = None
    days_overdue: int | None = None


class LoansListResponse(BaseModel):
    loans: list[LoanResponse]


class LoanHistoryItem(BaseModel):
    id: UUID
    book: BookSummary
    checked_out_at: str
    returned_at: str | None = None
    was_late: bool = False
    user_review: dict | None = None


class LoanHistoryResponse(BaseModel):
    loans: list[LoanHistoryItem]
    total: int
    page: int


class RenewResponse(BaseModel):
    loan_id: UUID
    new_due_date: str
    renewed_count: int
    can_renew_again: bool


class ReturnResponse(BaseModel):
    loan_id: UUID
    returned_at: str
    was_late: bool
    fine: dict | None = None
    reservation_triggered: bool = False
    next_reservation_user: str | None = None


class LostResponse(BaseModel):
    loan_id: UUID
    fine: dict | None = None
    copy_status: str = "lost"


class AdminLoanResponse(BaseModel):
    id: UUID
    user: dict
    book: dict
    checked_out_at: str
    due_date: str
    days_overdue: int | None = None
    status: str
    renewed_count: int

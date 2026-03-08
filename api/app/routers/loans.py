from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.loan import (
    AdminLoanResponse,
    CheckoutRequest,
    LoanHistoryResponse,
    LoanResponse,
    LoansListResponse,
    LostResponse,
    RenewResponse,
    ReturnResponse,
)
from app.services import loan_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Member endpoints
# ---------------------------------------------------------------------------


@router.post("/api/loans")
async def checkout_book(
    data: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.checkout_book(db, user, data.book_id)


@router.get("/api/loans", response_model=LoansListResponse)
async def get_my_loans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    loans = await loan_service.get_my_loans(db, user.id)
    return {"loans": loans}


# IMPORTANT: /history must be defined BEFORE /{loan_id} so "history" isn't
# captured as a UUID path parameter.
@router.get("/api/loans/history", response_model=LoanHistoryResponse)
async def get_loan_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.get_loan_history(db, user.id, page=page, limit=limit)


@router.get("/api/loans/{loan_id}", response_model=LoanResponse)
async def get_loan_detail(
    loan_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.get_loan_detail(db, user.id, loan_id)


@router.post("/api/loans/{loan_id}/renew", response_model=RenewResponse)
async def renew_loan(
    loan_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.renew_loan(db, user, loan_id)


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get("/api/admin/loans")
async def get_admin_loans(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.get_admin_loans(db, status=status, page=page, limit=limit)


@router.post("/api/admin/loans/{loan_id}/return", response_model=ReturnResponse)
async def process_return(
    loan_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.process_return(db, admin, loan_id)


@router.post("/api/admin/loans/{loan_id}/lost", response_model=LostResponse)
async def mark_lost(
    loan_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.mark_lost(db, admin, loan_id)

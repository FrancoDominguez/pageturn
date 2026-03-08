import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookCopy
from app.models.fine import Fine
from app.models.loan import Loan
from app.models.user import User
from app.services.loan_service import get_daily_rate


async def get_user_fines(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Get all fines for a user with totals and checkout-blocked status."""

    stmt = (
        select(Fine, Loan, BookCopy, Book)
        .join(Loan, Fine.loan_id == Loan.id)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(Fine.user_id == user_id)
        .order_by(Fine.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    fines = []
    total_outstanding = Decimal("0.00")

    for fine, loan, copy, book in rows:
        daily_rate = None
        days_overdue = None
        if fine.reason == "late_return" and loan.returned_at and loan.due_date:
            days_overdue = max(0, (loan.returned_at - loan.due_date).days)
            daily_rate = float(get_daily_rate(book.item_type))

        if fine.status == "pending":
            total_outstanding += fine.amount

        fines.append({
            "id": fine.id,
            "book_title": book.title,
            "book_author": book.author,
            "book_cover_url": book.cover_image_url,
            "loan_id": fine.loan_id,
            "amount": float(fine.amount),
            "daily_rate": daily_rate,
            "days_overdue": days_overdue,
            "reason": fine.reason,
            "status": fine.status,
            "created_at": fine.created_at.isoformat(),
        })

    checkout_blocked = total_outstanding >= Decimal("10.00")

    return {
        "fines": fines,
        "total_outstanding": float(total_outstanding),
        "checkout_blocked": checkout_blocked,
    }


def calculate_current_fine(
    item_type: str, due_date: datetime, now: datetime | None = None
) -> float:
    """
    Calculate the accrued fine for an active overdue loan (not yet stored).
    Returns 0.0 if not overdue.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if now <= due_date:
        return 0.0

    days_overdue = (now - due_date).days
    daily_rate = get_daily_rate(item_type)
    return float(days_overdue * daily_rate)


async def create_fine_for_return(db: AsyncSession, loan: Loan, book: Book) -> dict | None:
    """
    Create a fine record when a book is returned late.
    Returns the fine info dict, or None if not late.
    """
    now = datetime.now(timezone.utc)
    returned_at = loan.returned_at or now

    if returned_at <= loan.due_date:
        return None

    days_overdue = (returned_at - loan.due_date).days
    if days_overdue <= 0:
        return None

    daily_rate = get_daily_rate(book.item_type)
    amount = Decimal(str(days_overdue)) * daily_rate

    fine = Fine(
        user_id=loan.user_id,
        loan_id=loan.id,
        amount=amount,
        reason="late_return",
        status="pending",
    )
    db.add(fine)
    await db.flush()

    return {
        "id": str(fine.id),
        "amount": float(fine.amount),
        "days_overdue": days_overdue,
        "daily_rate": float(daily_rate),
        "reason": "late_return",
    }


async def waive_fine(
    db: AsyncSession, admin_id: uuid.UUID, fine_id: uuid.UUID
) -> dict:
    """Waive a fine (admin action)."""

    stmt = select(Fine).where(Fine.id == fine_id)
    result = await db.execute(stmt)
    fine = result.scalar_one_or_none()

    if not fine:
        raise HTTPException(status_code=404, detail="Fine not found")

    if fine.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot waive fine with status '{fine.status}'",
        )

    now = datetime.now(timezone.utc)
    fine.status = "waived"
    fine.waived_by = admin_id
    fine.waived_at = now

    await db.commit()
    await db.refresh(fine)

    return {
        "id": str(fine.id),
        "status": fine.status,
        "waived_by": str(admin_id),
        "waived_at": now.isoformat(),
        "message": "Fine waived successfully",
    }


async def get_admin_fines(
    db: AsyncSession,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Get all fines for admin view with pagination."""

    base_conditions = []
    if status:
        base_conditions.append(Fine.status == status)

    # Count total
    count_stmt = select(func.count(Fine.id))
    if base_conditions:
        count_stmt = count_stmt.where(and_(*base_conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Total outstanding amount
    outstanding_stmt = (
        select(func.coalesce(func.sum(Fine.amount), Decimal("0.00")))
        .where(Fine.status == "pending")
    )
    outstanding_result = await db.execute(outstanding_stmt)
    total_outstanding = outstanding_result.scalar_one()

    # Paginated query
    stmt = (
        select(Fine, Loan, BookCopy, Book, User)
        .join(Loan, Fine.loan_id == Loan.id)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .join(User, Fine.user_id == User.id)
    )
    if base_conditions:
        stmt = stmt.where(and_(*base_conditions))

    stmt = stmt.order_by(Fine.created_at.desc())
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    fines = []
    for fine, loan, copy, book, user in rows:
        fines.append({
            "id": fine.id,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "book_title": book.title,
            "amount": float(fine.amount),
            "reason": fine.reason,
            "status": fine.status,
            "created_at": fine.created_at.isoformat(),
        })

    return {
        "fines": fines,
        "total": total,
        "total_outstanding_amount": float(total_outstanding),
    }

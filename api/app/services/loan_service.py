import math
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book, BookCopy
from app.models.fine import Fine
from app.models.loan import Loan
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User


def get_loan_period(item_type: str) -> timedelta:
    """Return the loan period for a given item type."""
    periods = {
        "book": timedelta(days=14),
        "ebook": timedelta(days=14),
        "dvd": timedelta(days=7),
        "magazine": timedelta(days=7),
        "audiobook": timedelta(days=21),
    }
    return periods.get(item_type, timedelta(days=14))


def get_daily_rate(item_type: str) -> Decimal:
    """Return the daily fine rate for a given item type."""
    rates = {
        "book": Decimal("0.25"),
        "ebook": Decimal("0.25"),
        "dvd": Decimal("1.00"),
        "audiobook": Decimal("0.50"),
        "magazine": Decimal("0.10"),
    }
    return rates.get(item_type, Decimal("0.25"))


async def checkout_book(
    db: AsyncSession, user: User, book_id: uuid.UUID
) -> dict:
    """
    Check out a book or create a reservation.

    Steps:
    1. Check outstanding fines < $10
    2. Check active loans < max_loans
    3. Check not already checked out
    4. Check for ready reservation -> fulfill it
    5. Find available copy -> create loan
    6. No copy available -> create reservation
    """

    # 1. Check outstanding fines
    fines_stmt = (
        select(func.coalesce(func.sum(Fine.amount), Decimal("0.00")))
        .where(
            and_(
                Fine.user_id == user.id,
                Fine.status == "pending",
            )
        )
    )
    fines_result = await db.execute(fines_stmt)
    outstanding = fines_result.scalar_one()
    if outstanding >= Decimal("10.00"):
        raise HTTPException(
            status_code=403,
            detail=f"Outstanding fines (${outstanding:.2f}) exceed $10.00 limit. Please pay fines before checking out.",
        )

    # 2. Check active loan count
    active_loans_stmt = (
        select(func.count(Loan.id))
        .where(
            and_(
                Loan.user_id == user.id,
                Loan.status == "active",
            )
        )
    )
    active_result = await db.execute(active_loans_stmt)
    active_count = active_result.scalar_one()
    if active_count >= user.max_loans:
        raise HTTPException(
            status_code=403,
            detail=f"Maximum loan limit ({user.max_loans}) reached.",
        )

    # 3. Check not already checked out
    already_stmt = (
        select(Loan)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .where(
            and_(
                BookCopy.book_id == book_id,
                Loan.user_id == user.id,
                Loan.status == "active",
            )
        )
    )
    already_result = await db.execute(already_stmt)
    if already_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="You already have this book checked out.",
        )

    # Fetch the book to get item_type
    book_stmt = select(Book).where(Book.id == book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    loan_period = get_loan_period(book.item_type)
    now = datetime.now(timezone.utc)

    # 4. Check for a ready reservation for this user and book
    ready_res_stmt = (
        select(Reservation)
        .where(
            and_(
                Reservation.user_id == user.id,
                Reservation.book_id == book_id,
                Reservation.status == "ready",
            )
        )
    )
    ready_res_result = await db.execute(ready_res_stmt)
    ready_reservation = ready_res_result.scalar_one_or_none()

    if ready_reservation:
        # Find an available copy to fulfill the reservation
        copy_stmt = (
            select(BookCopy)
            .where(
                and_(
                    BookCopy.book_id == book_id,
                    BookCopy.status == "available",
                )
            )
            .limit(1)
        )
        copy_result = await db.execute(copy_stmt)
        copy = copy_result.scalar_one_or_none()

        if not copy:
            raise HTTPException(
                status_code=409,
                detail="Reserved copy is no longer available. Please contact staff.",
            )

        # Create loan
        loan = Loan(
            user_id=user.id,
            book_copy_id=copy.id,
            due_date=now + loan_period,
            status="active",
        )
        db.add(loan)
        copy.status = "checked_out"

        # Fulfill the reservation
        ready_reservation.status = "fulfilled"

        await db.commit()
        await db.refresh(loan)

        return {
            "action": "checked_out",
            "loan_id": str(loan.id),
            "due_date": loan.due_date.isoformat(),
            "message": "Reservation fulfilled. Book checked out successfully.",
        }

    # 5. Find an available copy
    copy_stmt = (
        select(BookCopy)
        .where(
            and_(
                BookCopy.book_id == book_id,
                BookCopy.status == "available",
            )
        )
        .limit(1)
    )
    copy_result = await db.execute(copy_stmt)
    copy = copy_result.scalar_one_or_none()

    if copy:
        loan = Loan(
            user_id=user.id,
            book_copy_id=copy.id,
            due_date=now + loan_period,
            status="active",
        )
        db.add(loan)
        copy.status = "checked_out"

        await db.commit()
        await db.refresh(loan)

        return {
            "action": "checked_out",
            "loan_id": str(loan.id),
            "due_date": loan.due_date.isoformat(),
            "message": "Book checked out successfully.",
        }

    # 6. No copy available -> create reservation
    from app.services.reservation_service import reserve_book

    reservation_result = await reserve_book(db, user, book_id)
    return {
        "action": "reserved",
        "reservation_id": reservation_result["id"],
        "queue_position": reservation_result.get("queue_position"),
        "message": "No copies available. You have been added to the waitlist.",
    }


async def get_my_loans(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """Get all active loans for a user with computed fields."""

    stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(
            and_(
                Loan.user_id == user_id,
                Loan.status == "active",
            )
        )
        .order_by(Loan.due_date.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    now = datetime.now(timezone.utc)
    loans = []
    for loan, copy, book in rows:
        days_remaining = (loan.due_date - now).days
        is_overdue = days_remaining < 0

        # Renewal eligibility
        can_renew = True
        renewal_blocked_reason = None

        if loan.renewed_count >= 2:
            can_renew = False
            renewal_blocked_reason = "Maximum renewals (2) reached"
        elif is_overdue and abs(days_remaining) > 7:
            can_renew = False
            renewal_blocked_reason = "Overdue by more than 7 days"
        else:
            # Check pending reservations
            res_stmt = (
                select(func.count(Reservation.id))
                .where(
                    and_(
                        Reservation.book_id == book.id,
                        Reservation.status == "pending",
                    )
                )
            )
            res_result = await db.execute(res_stmt)
            if res_result.scalar_one() > 0:
                can_renew = False
                renewal_blocked_reason = "Other patrons are waiting for this book"

        # Accrued fine for overdue
        accrued_fine = None
        daily_rate = None
        days_overdue = None
        if is_overdue:
            days_overdue = abs(days_remaining)
            daily_rate = float(get_daily_rate(book.item_type))
            accrued_fine = round(days_overdue * daily_rate, 2)

        loans.append({
            "id": loan.id,
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_image_url": book.cover_image_url,
            },
            "checked_out_at": loan.checked_out_at.isoformat(),
            "due_date": loan.due_date.isoformat(),
            "returned_at": None,
            "days_remaining": days_remaining,
            "renewed_count": loan.renewed_count,
            "can_renew": can_renew,
            "renewal_blocked_reason": renewal_blocked_reason,
            "status": loan.status,
            "accrued_fine": accrued_fine,
            "daily_rate": daily_rate,
            "days_overdue": days_overdue,
        })

    return loans


async def get_loan_detail(
    db: AsyncSession, user_id: uuid.UUID, loan_id: uuid.UUID
) -> dict:
    """Get a single loan with computed fields."""

    stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(
            and_(
                Loan.id == loan_id,
                Loan.user_id == user_id,
            )
        )
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan, copy, book = row
    now = datetime.now(timezone.utc)
    days_remaining = (loan.due_date - now).days
    is_overdue = days_remaining < 0

    can_renew = True
    renewal_blocked_reason = None

    if loan.status != "active":
        can_renew = False
        renewal_blocked_reason = "Loan is not active"
    elif loan.renewed_count >= 2:
        can_renew = False
        renewal_blocked_reason = "Maximum renewals (2) reached"
    elif is_overdue and abs(days_remaining) > 7:
        can_renew = False
        renewal_blocked_reason = "Overdue by more than 7 days"
    else:
        res_stmt = (
            select(func.count(Reservation.id))
            .where(
                and_(
                    Reservation.book_id == book.id,
                    Reservation.status == "pending",
                )
            )
        )
        res_result = await db.execute(res_stmt)
        if res_result.scalar_one() > 0:
            can_renew = False
            renewal_blocked_reason = "Other patrons are waiting for this book"

    accrued_fine = None
    daily_rate = None
    days_overdue = None
    if is_overdue and loan.status == "active":
        days_overdue = abs(days_remaining)
        daily_rate = float(get_daily_rate(book.item_type))
        accrued_fine = round(days_overdue * daily_rate, 2)

    return {
        "id": loan.id,
        "book": {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "cover_image_url": book.cover_image_url,
        },
        "checked_out_at": loan.checked_out_at.isoformat(),
        "due_date": loan.due_date.isoformat(),
        "returned_at": loan.returned_at.isoformat() if loan.returned_at else None,
        "days_remaining": days_remaining,
        "renewed_count": loan.renewed_count,
        "can_renew": can_renew,
        "renewal_blocked_reason": renewal_blocked_reason,
        "status": loan.status,
        "accrued_fine": accrued_fine,
        "daily_rate": daily_rate,
        "days_overdue": days_overdue,
    }


async def get_loan_history(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, limit: int = 20
) -> dict:
    """Get returned loans with review status."""

    base_stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(
            and_(
                Loan.user_id == user_id,
                Loan.status == "returned",
            )
        )
    )

    # Count
    count_stmt = (
        select(func.count(Loan.id))
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .where(
            and_(
                Loan.user_id == user_id,
                Loan.status == "returned",
            )
        )
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Paginated results
    offset = (page - 1) * limit
    stmt = base_stmt.order_by(Loan.returned_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    loans = []
    for loan, copy, book in rows:
        # Check if user has reviewed this book
        review_stmt = (
            select(Review)
            .where(
                and_(
                    Review.user_id == user_id,
                    Review.book_id == book.id,
                )
            )
        )
        review_result = await db.execute(review_stmt)
        review = review_result.scalar_one_or_none()

        user_review = None
        if review:
            user_review = {
                "id": str(review.id),
                "rating": review.rating,
                "review_text": review.review_text,
            }

        was_late = False
        if loan.returned_at and loan.due_date:
            was_late = loan.returned_at > loan.due_date

        loans.append({
            "id": loan.id,
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_image_url": book.cover_image_url,
            },
            "checked_out_at": loan.checked_out_at.isoformat(),
            "returned_at": loan.returned_at.isoformat() if loan.returned_at else None,
            "was_late": was_late,
            "user_review": user_review,
        })

    return {
        "loans": loans,
        "total": total,
        "page": page,
    }


async def renew_loan(
    db: AsyncSession, user: User, loan_id: uuid.UUID
) -> dict:
    """
    Renew a loan.

    Checks:
    1. Verify ownership and active status
    2. Check renewed_count < 2
    3. Check no pending reservations for the book
    4. Check not overdue > 7 days
    5. Update due_date and renewed_count
    """

    stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(Loan.id == loan_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan, copy, book = row

    # 1. Verify ownership and active status
    if loan.user_id != user.id:
        raise HTTPException(status_code=403, detail="This is not your loan")
    if loan.status != "active":
        raise HTTPException(status_code=409, detail="Loan is not active")

    # 2. Check renewal limit
    if loan.renewed_count >= 2:
        raise HTTPException(
            status_code=409,
            detail="Maximum renewals (2) reached",
        )

    now = datetime.now(timezone.utc)

    # 3. Check pending reservations
    res_stmt = (
        select(func.count(Reservation.id))
        .where(
            and_(
                Reservation.book_id == book.id,
                Reservation.status == "pending",
            )
        )
    )
    res_result = await db.execute(res_stmt)
    if res_result.scalar_one() > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot renew: other patrons are waiting for this book",
        )

    # 4. Check not overdue > 7 days
    days_overdue = (now - loan.due_date).days
    if days_overdue > 7:
        raise HTTPException(
            status_code=409,
            detail="Cannot renew: loan is overdue by more than 7 days",
        )

    # 5. Update due_date and renewed_count
    loan_period = get_loan_period(book.item_type)
    loan.due_date = now + loan_period
    loan.renewed_count += 1

    await db.commit()
    await db.refresh(loan)

    return {
        "loan_id": loan.id,
        "new_due_date": loan.due_date.isoformat(),
        "renewed_count": loan.renewed_count,
        "can_renew_again": loan.renewed_count < 2,
    }


async def process_return(
    db: AsyncSession, admin: User, loan_id: uuid.UUID
) -> dict:
    """Process a book return: mark returned, calculate fine, trigger reservation queue."""

    stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(Loan.id == loan_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan, copy, book = row

    if loan.status != "active":
        raise HTTPException(status_code=409, detail="Loan is not active")

    now = datetime.now(timezone.utc)

    # Mark as returned
    loan.status = "returned"
    loan.returned_at = now
    copy.status = "available"

    # Calculate fine
    fine_info = None
    was_late = now > loan.due_date
    if was_late:
        from app.services.fine_service import create_fine_for_return

        fine_info = await create_fine_for_return(db, loan, book)

    # Trigger reservation queue
    from app.services.reservation_service import process_return_queue

    reservation_triggered = False
    next_user = None
    queue_result = await process_return_queue(db, book.id)
    if queue_result:
        reservation_triggered = True
        next_user = queue_result.get("user_email")
        # The copy has been reserved, mark it accordingly
        copy.status = "reserved"

    await db.commit()

    return {
        "loan_id": loan.id,
        "returned_at": now.isoformat(),
        "was_late": was_late,
        "fine": fine_info,
        "reservation_triggered": reservation_triggered,
        "next_reservation_user": next_user,
    }


async def mark_lost(
    db: AsyncSession, admin: User, loan_id: uuid.UUID
) -> dict:
    """Mark a loan item as lost, create a lost item fine, and update copy status."""

    stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(Loan.id == loan_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan, copy, book = row

    if loan.status not in ("active", "overdue"):
        raise HTTPException(status_code=409, detail="Loan is not active")

    now = datetime.now(timezone.utc)

    # Mark loan as lost
    loan.status = "lost"
    loan.returned_at = now

    # Mark copy as lost
    copy.status = "lost"

    # Create lost item fine (replacement cost or default $25)
    amount = book.replacement_cost if book.replacement_cost else Decimal("25.00")
    fine = Fine(
        user_id=loan.user_id,
        loan_id=loan.id,
        amount=amount,
        reason="lost_item",
        status="pending",
    )
    db.add(fine)

    await db.commit()
    await db.refresh(fine)

    return {
        "loan_id": loan.id,
        "fine": {
            "id": str(fine.id),
            "amount": float(fine.amount),
            "reason": fine.reason,
        },
        "copy_status": "lost",
    }


async def get_admin_loans(
    db: AsyncSession,
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Get all loans for admin view."""

    base_conditions = []
    if status:
        base_conditions.append(Loan.status == status)

    # Count
    count_stmt = select(func.count(Loan.id))
    if base_conditions:
        count_stmt = count_stmt.where(and_(*base_conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Paginated query
    stmt = (
        select(Loan, BookCopy, Book, User)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .join(User, Loan.user_id == User.id)
    )
    if base_conditions:
        stmt = stmt.where(and_(*base_conditions))

    stmt = stmt.order_by(Loan.created_at.desc())
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    now = datetime.now(timezone.utc)
    loans = []
    for loan, copy, book, user in rows:
        days_overdue = None
        if loan.status == "active" and now > loan.due_date:
            days_overdue = (now - loan.due_date).days

        loans.append({
            "id": loan.id,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "book": {
                "id": str(book.id),
                "title": book.title,
                "author": book.author,
                "cover_image_url": book.cover_image_url,
            },
            "checked_out_at": loan.checked_out_at.isoformat(),
            "due_date": loan.due_date.isoformat(),
            "days_overdue": days_overdue,
            "status": loan.status,
            "renewed_count": loan.renewed_count,
        })

    return {
        "loans": loans,
        "total": total,
        "page": page,
    }

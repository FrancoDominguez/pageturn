import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book, BookCopy
from app.models.loan import Loan
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate


async def _build_copies_list(db: AsyncSession, copies: list, is_admin: bool) -> list[dict]:
    """Build copies list, enriching with borrower info for admins."""
    copy_dicts = []
    # If admin, batch-fetch active loans with users for all checked-out copies
    borrower_map: dict[uuid.UUID, dict] = {}
    if is_admin:
        checked_out_ids = [c.id for c in copies if c.status == "checked_out"]
        if checked_out_ids:
            stmt = (
                select(Loan, User)
                .join(User, Loan.user_id == User.id)
                .where(
                    and_(
                        Loan.book_copy_id.in_(checked_out_ids),
                        Loan.status.in_(["active", "overdue"]),
                    )
                )
            )
            result = await db.execute(stmt)
            for loan, user in result.all():
                borrower_map[loan.book_copy_id] = {
                    "user_id": str(user.id),
                    "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
                    "email": user.email,
                    "due_date": loan.due_date.isoformat(),
                    "loan_id": str(loan.id),
                    "status": loan.status,
                }

    for c in copies:
        entry = {
            "id": c.id,
            "status": c.status,
            "condition": c.condition,
            "barcode": c.barcode,
        }
        if is_admin and c.id in borrower_map:
            entry["current_borrower"] = borrower_map[c.id]
        copy_dicts.append(entry)
    return copy_dicts


async def get_book_detail(
    db: AsyncSession, book_id: uuid.UUID, user_id: uuid.UUID | None = None, is_admin: bool = False
) -> dict:
    """Get full book detail including copies, availability, and user context."""

    # Fetch book with copies eagerly loaded
    stmt = (
        select(Book)
        .options(selectinload(Book.copies))
        .where(Book.id == book_id)
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    copies = book.copies
    total_copies = len(copies)
    available_copies = sum(1 for c in copies if c.status == "available")

    # Earliest return date for checked-out copies
    earliest_return = None
    if available_copies == 0 and total_copies > 0:
        checked_out_copy_ids = [c.id for c in copies if c.status == "checked_out"]
        if checked_out_copy_ids:
            loan_stmt = (
                select(func.min(Loan.due_date))
                .where(
                    and_(
                        Loan.book_copy_id.in_(checked_out_copy_ids),
                        Loan.status == "active",
                    )
                )
            )
            loan_result = await db.execute(loan_stmt)
            earliest_dt = loan_result.scalar_one_or_none()
            if earliest_dt:
                earliest_return = earliest_dt.isoformat()

    # Count active reservations for this book
    res_count_stmt = (
        select(func.count(Reservation.id))
        .where(
            and_(
                Reservation.book_id == book_id,
                Reservation.status.in_(["pending", "ready"]),
            )
        )
    )
    res_count_result = await db.execute(res_count_stmt)
    reservation_count = res_count_result.scalar_one()

    # User-specific context
    user_loan = None
    user_reservation = None
    if user_id:
        # Most recent loan for this book by this user (active/overdue first, then returned)
        user_loan_stmt = (
            select(Loan)
            .join(BookCopy, Loan.book_copy_id == BookCopy.id)
            .where(
                and_(
                    BookCopy.book_id == book_id,
                    Loan.user_id == user_id,
                    Loan.status.in_(["active", "overdue", "returned"]),
                )
            )
            .order_by(
                # Prioritize active/overdue over returned
                (Loan.status == "returned").asc(),
                Loan.checked_out_at.desc(),
            )
            .limit(1)
        )
        user_loan_result = await db.execute(user_loan_stmt)
        loan_obj = user_loan_result.scalar_one_or_none()
        if loan_obj:
            user_loan = {
                "id": str(loan_obj.id),
                "status": loan_obj.status,
                "due_date": loan_obj.due_date.isoformat(),
                "renewed_count": loan_obj.renewed_count,
            }

        # Active reservation for this book by this user
        user_res_stmt = (
            select(Reservation)
            .where(
                and_(
                    Reservation.book_id == book_id,
                    Reservation.user_id == user_id,
                    Reservation.status.in_(["pending", "ready"]),
                )
            )
        )
        user_res_result = await db.execute(user_res_stmt)
        res_obj = user_res_result.scalar_one_or_none()
        if res_obj:
            user_reservation = {
                "id": str(res_obj.id),
                "status": res_obj.status,
                "queue_position": res_obj.queue_position,
                "expires_at": res_obj.expires_at.isoformat() if res_obj.expires_at else None,
            }

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "isbn13": book.isbn13,
        "description": book.description,
        "genre": book.genre,
        "genres": book.genres or [],
        "item_type": book.item_type,
        "cover_image_url": book.cover_image_url,
        "page_count": book.page_count,
        "publication_year": book.publication_year,
        "publisher": book.publisher,
        "language": book.language,
        "avg_rating": float(book.avg_rating) if book.avg_rating else 0.0,
        "rating_count": book.rating_count,
        "is_staff_pick": book.is_staff_pick,
        "staff_pick_note": book.staff_pick_note,
        "copies": await _build_copies_list(db, copies, is_admin),
        "available_copies": available_copies,
        "total_copies": total_copies,
        "earliest_return_date": earliest_return,
        "reservation_count": reservation_count,
        "user_loan": user_loan,
        "user_reservation": user_reservation,
    }


async def create_book(db: AsyncSession, data: BookCreate) -> dict:
    """Create a new book with initial copies."""

    book = Book(
        title=data.title,
        author=data.author,
        isbn=data.isbn,
        isbn13=data.isbn13,
        description=data.description,
        genre=data.genre,
        genres=data.genres,
        item_type=data.item_type,
        cover_image_url=data.cover_image_url,
        page_count=data.page_count,
        publication_year=data.publication_year,
        publisher=data.publisher,
        language=data.language,
        is_staff_pick=data.is_staff_pick,
        staff_pick_note=data.staff_pick_note,
    )
    db.add(book)
    await db.flush()  # Get book.id before creating copies

    # Generate copies
    copies = []
    for i in range(1, data.copies + 1):
        barcode = _generate_barcode(book.id, i)
        copy = BookCopy(
            book_id=book.id,
            barcode=barcode,
            condition=data.copy_condition,
            status="available",
        )
        db.add(copy)
        copies.append(copy)

    await db.commit()
    await db.refresh(book)

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "copies_created": len(copies),
    }


async def update_book(
    db: AsyncSession, book_id: uuid.UUID, data: BookUpdate
) -> dict:
    """Partial update of book metadata."""

    stmt = select(Book).where(Book.id == book_id)
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)

    book.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(book)

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "message": "Book updated successfully",
    }


async def delete_book(db: AsyncSession, book_id: uuid.UUID) -> dict:
    """Delete a book if no active loans exist."""

    stmt = select(Book).options(selectinload(Book.copies)).where(Book.id == book_id)
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check for active loans on any copy
    copy_ids = [c.id for c in book.copies]
    if copy_ids:
        active_loan_stmt = (
            select(func.count(Loan.id))
            .where(
                and_(
                    Loan.book_copy_id.in_(copy_ids),
                    Loan.status == "active",
                )
            )
        )
        active_result = await db.execute(active_loan_stmt)
        active_count = active_result.scalar_one()
        if active_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete book with {active_count} active loan(s)",
            )

    await db.delete(book)
    await db.commit()

    return {"message": "Book deleted successfully"}


async def add_copies(
    db: AsyncSession,
    book_id: uuid.UUID,
    count: int = 1,
    condition: str = "new",
) -> list[dict]:
    """Add new copies to an existing book."""

    stmt = select(Book).where(Book.id == book_id)
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Find the highest existing copy number for barcode generation
    existing_stmt = (
        select(func.count(BookCopy.id))
        .where(BookCopy.book_id == book_id)
    )
    existing_result = await db.execute(existing_stmt)
    existing_count = existing_result.scalar_one()

    copies = []
    for i in range(1, count + 1):
        copy_number = existing_count + i
        barcode = _generate_barcode(book_id, copy_number)
        copy = BookCopy(
            book_id=book_id,
            barcode=barcode,
            condition=condition,
            status="available",
        )
        db.add(copy)
        copies.append(copy)

    await db.commit()

    return [
        {
            "id": c.id,
            "barcode": c.barcode,
            "condition": c.condition,
            "status": c.status,
        }
        for c in copies
    ]


async def update_copy(
    db: AsyncSession,
    copy_id: uuid.UUID,
    status: str | None = None,
    condition: str | None = None,
) -> dict:
    """Update status or condition of a specific book copy."""

    stmt = select(BookCopy).where(BookCopy.id == copy_id)
    result = await db.execute(stmt)
    copy = result.scalar_one_or_none()

    if not copy:
        raise HTTPException(status_code=404, detail="Copy not found")

    if status is not None:
        copy.status = status
    if condition is not None:
        copy.condition = condition

    await db.commit()
    await db.refresh(copy)

    return {
        "id": copy.id,
        "barcode": copy.barcode,
        "status": copy.status,
        "condition": copy.condition,
    }


def _generate_barcode(book_id: uuid.UUID, copy_number: int) -> str:
    """Generate barcode in format PT-XXXX-NN where XXXX is from the book UUID."""
    short_id = str(book_id).split("-")[0].upper()[:4]
    return f"PT-{short_id}-{copy_number:02d}"

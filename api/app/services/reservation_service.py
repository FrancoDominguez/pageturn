import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookCopy
from app.models.loan import Loan
from app.models.reservation import Reservation
from app.models.user import User


async def reserve_book(
    db: AsyncSession, user: User, book_id: uuid.UUID
) -> dict:
    """
    Reserve a book.

    1. Check not already reserved or checked out
    2. Find available copy -> immediate reserve (status='ready', expires_at=now+48h)
    3. No copy -> waitlist (status='pending', queue_position=max+1)
    """

    # Verify book exists
    book_stmt = select(Book).where(Book.id == book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 1. Check not already reserved
    existing_res_stmt = (
        select(Reservation)
        .where(
            and_(
                Reservation.user_id == user.id,
                Reservation.book_id == book_id,
                Reservation.status.in_(["pending", "ready"]),
            )
        )
    )
    existing_res_result = await db.execute(existing_res_stmt)
    if existing_res_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="You already have an active reservation for this book",
        )

    # Check not already checked out
    checked_out_stmt = (
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
    checked_out_result = await db.execute(checked_out_stmt)
    if checked_out_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="You already have this book checked out",
        )

    now = datetime.now(timezone.utc)

    # 2. Find available copy for immediate reservation
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
    available_copy = copy_result.scalar_one_or_none()

    if available_copy:
        reservation = Reservation(
            user_id=user.id,
            book_id=book_id,
            status="ready",
            expires_at=now + timedelta(hours=48),
            queue_position=None,
        )
        db.add(reservation)
        available_copy.status = "reserved"

        await db.commit()
        await db.refresh(reservation)

        return {
            "id": str(reservation.id),
            "status": "ready",
            "expires_at": reservation.expires_at.isoformat(),
            "queue_position": None,
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_image_url": book.cover_image_url,
            },
            "reserved_at": reservation.reserved_at.isoformat(),
        }

    # 3. No copy available -> waitlist
    max_pos_stmt = (
        select(func.coalesce(func.max(Reservation.queue_position), 0))
        .where(
            and_(
                Reservation.book_id == book_id,
                Reservation.status == "pending",
            )
        )
    )
    max_pos_result = await db.execute(max_pos_stmt)
    max_pos = max_pos_result.scalar_one()

    reservation = Reservation(
        user_id=user.id,
        book_id=book_id,
        status="pending",
        queue_position=max_pos + 1,
    )
    db.add(reservation)

    await db.commit()
    await db.refresh(reservation)

    return {
        "id": str(reservation.id),
        "status": "pending",
        "queue_position": reservation.queue_position,
        "expires_at": None,
        "book": {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "cover_image_url": book.cover_image_url,
        },
        "reserved_at": reservation.reserved_at.isoformat(),
    }


async def get_my_reservations(
    db: AsyncSession, user_id: uuid.UUID
) -> list[dict]:
    """Get all active reservations for a user."""

    stmt = (
        select(Reservation, Book)
        .join(Book, Reservation.book_id == Book.id)
        .where(
            and_(
                Reservation.user_id == user_id,
                Reservation.status.in_(["pending", "ready"]),
            )
        )
        .order_by(Reservation.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    reservations = []
    for reservation, book in rows:
        reservations.append({
            "id": reservation.id,
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_image_url": book.cover_image_url,
            },
            "status": reservation.status,
            "queue_position": reservation.queue_position,
            "expires_at": reservation.expires_at.isoformat() if reservation.expires_at else None,
            "reserved_at": reservation.reserved_at.isoformat(),
        })

    return reservations


async def cancel_reservation(
    db: AsyncSession, user: User, reservation_id: uuid.UUID
) -> dict:
    """
    Cancel a reservation.

    1. Set status='cancelled'
    2. If was 'ready', set copy back to available, check next in queue
    3. If was 'pending', decrement queue_positions for same book
    """

    stmt = select(Reservation).where(Reservation.id == reservation_id)
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.user_id != user.id:
        raise HTTPException(status_code=403, detail="This is not your reservation")

    if reservation.status not in ("pending", "ready"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel reservation with status '{reservation.status}'",
        )

    old_status = reservation.status
    book_id = reservation.book_id

    # 1. Cancel the reservation
    reservation.status = "cancelled"

    if old_status == "ready":
        # 2. Find the reserved copy and set back to available
        # Then check if next person in queue should get it
        copy_stmt = (
            select(BookCopy)
            .where(
                and_(
                    BookCopy.book_id == book_id,
                    BookCopy.status == "reserved",
                )
            )
            .limit(1)
        )
        copy_result = await db.execute(copy_stmt)
        reserved_copy = copy_result.scalar_one_or_none()

        if reserved_copy:
            reserved_copy.status = "available"

        # Check next in queue
        await db.flush()
        await process_return_queue(db, book_id)

    elif old_status == "pending":
        # 3. Decrement queue_positions for later reservations of the same book
        queue_pos = reservation.queue_position
        if queue_pos is not None:
            later_stmt = (
                select(Reservation)
                .where(
                    and_(
                        Reservation.book_id == book_id,
                        Reservation.status == "pending",
                        Reservation.queue_position > queue_pos,
                    )
                )
                .order_by(Reservation.queue_position.asc())
            )
            later_result = await db.execute(later_stmt)
            later_reservations = later_result.scalars().all()

            for res in later_reservations:
                res.queue_position -= 1

    await db.commit()

    return {"message": "Reservation cancelled successfully"}


async def process_return_queue(
    db: AsyncSession, book_id: uuid.UUID
) -> dict | None:
    """
    Process the reservation queue when a book becomes available.
    Find the next pending reservation and set it to ready.
    Returns info about the notified user, or None if no one is waiting.
    """

    # Find next pending reservation (lowest queue_position)
    stmt = (
        select(Reservation, User)
        .join(User, Reservation.user_id == User.id)
        .where(
            and_(
                Reservation.book_id == book_id,
                Reservation.status == "pending",
            )
        )
        .order_by(Reservation.queue_position.asc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        return None

    reservation, user = row

    now = datetime.now(timezone.utc)
    reservation.status = "ready"
    reservation.expires_at = now + timedelta(hours=48)
    reservation.notified_at = now
    reservation.queue_position = None

    # Decrement positions for remaining pending reservations
    remaining_stmt = (
        select(Reservation)
        .where(
            and_(
                Reservation.book_id == book_id,
                Reservation.status == "pending",
                Reservation.queue_position.is_not(None),
            )
        )
        .order_by(Reservation.queue_position.asc())
    )
    remaining_result = await db.execute(remaining_stmt)
    remaining = remaining_result.scalars().all()

    for i, res in enumerate(remaining, start=1):
        res.queue_position = i

    await db.flush()

    return {
        "reservation_id": str(reservation.id),
        "user_id": str(user.id),
        "user_email": user.email,
        "expires_at": reservation.expires_at.isoformat(),
    }


async def expire_reservations(db: AsyncSession) -> int:
    """
    Cron job: Expire ready reservations past their expires_at.
    Returns the number of expired reservations.
    """

    now = datetime.now(timezone.utc)

    stmt = (
        select(Reservation)
        .where(
            and_(
                Reservation.status == "ready",
                Reservation.expires_at < now,
            )
        )
    )
    result = await db.execute(stmt)
    expired_reservations = result.scalars().all()

    count = 0
    for reservation in expired_reservations:
        reservation.status = "expired"
        book_id = reservation.book_id

        # Release the reserved copy
        copy_stmt = (
            select(BookCopy)
            .where(
                and_(
                    BookCopy.book_id == book_id,
                    BookCopy.status == "reserved",
                )
            )
            .limit(1)
        )
        copy_result = await db.execute(copy_stmt)
        reserved_copy = copy_result.scalar_one_or_none()

        if reserved_copy:
            reserved_copy.status = "available"

        # Check if next person in queue should get it
        await db.flush()
        await process_return_queue(db, book_id)

        count += 1

    await db.commit()

    return count

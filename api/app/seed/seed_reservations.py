"""Seed mock reservations."""

import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookCopy
from app.models.loan import Loan
from app.models.reservation import Reservation
from app.models.user import User

random.seed(42)

PENDING_COUNT = 15
READY_COUNT = 10
FULFILLED_COUNT = 5


async def seed_reservations(db: AsyncSession) -> None:
    """Generate 30 reservations: 15 pending, 10 ready, 5 fulfilled."""
    print("Seeding 30 reservations...")

    now = datetime.now(timezone.utc)

    # Fetch user IDs (non-admin preferred)
    users_result = await db.execute(select(User.id).where(User.role == "user"))
    user_ids = [row[0] for row in users_result.fetchall()]

    if not user_ids:
        print("  ERROR: No users found. Run seed_users first.")
        return

    reservation_records = []
    used_user_book_pairs = set()

    # --- PENDING RESERVATIONS (15) ---
    # Find books where ALL copies are checked_out
    all_checked_out_result = await db.execute(
        select(Book.id)
        .join(BookCopy, BookCopy.book_id == Book.id)
        .group_by(Book.id)
        .having(
            func.sum(case((BookCopy.status == "checked_out", 1), else_=0))
            == func.count(BookCopy.id)
        )
    )
    fully_checked_out_book_ids = [row[0] for row in all_checked_out_result.fetchall()]

    pending_books = fully_checked_out_book_ids[:PENDING_COUNT] if len(fully_checked_out_book_ids) >= PENDING_COUNT else fully_checked_out_book_ids
    print(f"  Found {len(fully_checked_out_book_ids)} fully checked-out books for pending reservations")

    # Assign queue positions per book
    book_queue: dict[uuid.UUID, int] = {}
    for book_id in pending_books:
        user_id = random.choice(user_ids)
        pair = (user_id, book_id)
        # Avoid duplicate user+book
        attempts = 0
        while pair in used_user_book_pairs and attempts < 20:
            user_id = random.choice(user_ids)
            pair = (user_id, book_id)
            attempts += 1
        used_user_book_pairs.add(pair)

        queue_pos = book_queue.get(book_id, 0) + 1
        book_queue[book_id] = queue_pos

        reserved_at = now - timedelta(days=random.randint(1, 14))

        reservation_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "book_id": book_id,
            "reserved_at": reserved_at,
            "expires_at": None,
            "status": "pending",
            "queue_position": queue_pos,
            "notified_at": None,
            "created_at": reserved_at,
        })

    # --- READY RESERVATIONS (10) ---
    # Find books with at least one available copy
    available_copies_result = await db.execute(
        select(BookCopy.id, BookCopy.book_id)
        .where(BookCopy.status == "available")
        .limit(READY_COUNT * 2)  # fetch extra in case of conflicts
    )
    available_copies = available_copies_result.fetchall()

    ready_copies_to_reserve = []
    ready_count = 0
    for copy_id, book_id in available_copies:
        if ready_count >= READY_COUNT:
            break

        user_id = random.choice(user_ids)
        pair = (user_id, book_id)
        attempts = 0
        while pair in used_user_book_pairs and attempts < 20:
            user_id = random.choice(user_ids)
            pair = (user_id, book_id)
            attempts += 1
        if pair in used_user_book_pairs:
            continue
        used_user_book_pairs.add(pair)

        reserved_at = now - timedelta(hours=random.randint(1, 24))
        expires_at = now + timedelta(hours=random.randint(24, 48))

        reservation_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "book_id": book_id,
            "reserved_at": reserved_at,
            "expires_at": expires_at,
            "status": "ready",
            "queue_position": None,
            "notified_at": reserved_at + timedelta(minutes=random.randint(5, 60)),
            "created_at": reserved_at,
        })

        ready_copies_to_reserve.append(copy_id)
        ready_count += 1

    # --- FULFILLED RESERVATIONS (5) ---
    # Find returned loans to link to
    returned_loans_result = await db.execute(
        select(Loan.user_id, Loan.book_copy_id)
        .join(BookCopy, BookCopy.id == Loan.book_copy_id)
        .where(Loan.status == "returned")
        .limit(FULFILLED_COUNT * 3)
    )
    returned_loans = returned_loans_result.fetchall()

    # Get book_ids for those copies
    fulfilled_count = 0
    for user_id, copy_id in returned_loans:
        if fulfilled_count >= FULFILLED_COUNT:
            break

        copy_book_result = await db.execute(
            select(BookCopy.book_id).where(BookCopy.id == copy_id)
        )
        book_id_row = copy_book_result.fetchone()
        if not book_id_row:
            continue
        book_id = book_id_row[0]

        pair = (user_id, book_id)
        if pair in used_user_book_pairs:
            continue
        used_user_book_pairs.add(pair)

        reserved_at = now - timedelta(days=random.randint(14, 60))

        reservation_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "book_id": book_id,
            "reserved_at": reserved_at,
            "expires_at": reserved_at + timedelta(hours=48),
            "status": "fulfilled",
            "queue_position": None,
            "notified_at": reserved_at + timedelta(minutes=30),
            "created_at": reserved_at,
        })
        fulfilled_count += 1

    # Batch insert reservations
    if reservation_records:
        await db.execute(insert(Reservation), reservation_records)

    # Update copies for ready reservations to 'reserved'
    if ready_copies_to_reserve:
        print(f"  Marking {len(ready_copies_to_reserve)} copies as reserved...")
        await db.execute(
            update(BookCopy)
            .where(BookCopy.id.in_(ready_copies_to_reserve))
            .values(status="reserved")
        )

    await db.commit()

    pending_actual = sum(1 for r in reservation_records if r["status"] == "pending")
    ready_actual = sum(1 for r in reservation_records if r["status"] == "ready")
    fulfilled_actual = sum(1 for r in reservation_records if r["status"] == "fulfilled")
    print(f"  Seeded {len(reservation_records)} reservations ({pending_actual} pending, {ready_actual} ready, {fulfilled_actual} fulfilled)")

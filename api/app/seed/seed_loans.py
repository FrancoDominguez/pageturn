"""Seed mock loans."""

import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookCopy
from app.models.loan import Loan
from app.models.user import User

random.seed(42)

# Loan period by item type (days)
LOAN_PERIODS = {
    "book": 21,
    "ebook": 14,
    "audiobook": 14,
    "dvd": 7,
    "magazine": 7,
}

TOTAL_LOANS = 500
RETURNED_COUNT = 400
ACTIVE_COUNT = 75
OVERDUE_COUNT = 25


async def seed_loans(db: AsyncSession) -> None:
    """Generate 500 mock loans: 400 returned, 75 active, 25 overdue."""
    print("Seeding 500 loans...")

    now = datetime.now(timezone.utc)

    # Fetch all users and book copies with their book's item_type
    users_result = await db.execute(select(User.id))
    user_ids = [row[0] for row in users_result.fetchall()]

    copies_result = await db.execute(
        select(BookCopy.id, BookCopy.book_id, Book.item_type)
        .join(Book, BookCopy.book_id == Book.id)
    )
    all_copies = copies_result.fetchall()  # list of (copy_id, book_id, item_type)

    if not user_ids or not all_copies:
        print("  ERROR: No users or book copies found. Run seed_books and seed_users first.")
        return

    # Create a weighted user distribution: some heavy readers, some light
    # First 10 users get more loans (heavy readers)
    heavy_readers = user_ids[:10]
    medium_readers = user_ids[10:30]
    light_readers = user_ids[30:]

    def pick_user() -> uuid.UUID:
        r = random.random()
        if r < 0.4:
            return random.choice(heavy_readers)
        elif r < 0.8:
            return random.choice(medium_readers) if medium_readers else random.choice(heavy_readers)
        else:
            return random.choice(light_readers) if light_readers else random.choice(heavy_readers)

    # Shuffle copies for assignment
    available_copies = list(all_copies)
    random.shuffle(available_copies)

    loan_records = []
    checked_out_copy_ids = set()  # track copies currently checked out

    # --- RETURNED LOANS (400) ---
    for _ in range(RETURNED_COUNT):
        copy_id, book_id, item_type = random.choice(available_copies)
        user_id = pick_user()

        loan_period = LOAN_PERIODS.get(item_type, 21)

        # Checked out 1-12 months ago
        days_ago = random.randint(14, 365)
        checked_out_at = now - timedelta(days=days_ago)

        renewed_count = random.choices([0, 1, 2], weights=[70, 20, 10], k=1)[0]
        due_date = checked_out_at + timedelta(days=loan_period * (1 + renewed_count))

        # Return: some on time, some late (up to 14 days)
        return_offset = random.randint(-3, 14)
        returned_at = due_date + timedelta(days=return_offset)

        # Don't return in the future
        if returned_at > now:
            returned_at = now - timedelta(hours=random.randint(1, 48))

        loan_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "book_copy_id": copy_id,
            "checked_out_at": checked_out_at,
            "due_date": due_date,
            "returned_at": returned_at,
            "renewed_count": renewed_count,
            "status": "returned",
            "created_at": checked_out_at,
        })

    # --- ACTIVE LOANS (75) ---
    # These need unique copies that aren't already checked out
    active_copy_pool = [c for c in available_copies if c[0] not in checked_out_copy_ids]
    random.shuffle(active_copy_pool)

    for i in range(min(ACTIVE_COUNT, len(active_copy_pool))):
        copy_id, book_id, item_type = active_copy_pool[i]
        checked_out_copy_ids.add(copy_id)
        user_id = pick_user()

        loan_period = LOAN_PERIODS.get(item_type, 21)

        # Checked out within last 3 weeks
        days_ago = random.randint(1, 21)
        checked_out_at = now - timedelta(days=days_ago)

        renewed_count = random.choices([0, 1], weights=[80, 20], k=1)[0]
        due_date = checked_out_at + timedelta(days=loan_period * (1 + renewed_count))

        # Ensure due date is in the future
        if due_date <= now:
            due_date = now + timedelta(days=random.randint(1, 14))

        loan_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "book_copy_id": copy_id,
            "checked_out_at": checked_out_at,
            "due_date": due_date,
            "returned_at": None,
            "renewed_count": renewed_count,
            "status": "active",
            "created_at": checked_out_at,
        })

    # --- OVERDUE LOANS (25) ---
    overdue_copy_pool = [c for c in available_copies if c[0] not in checked_out_copy_ids]
    random.shuffle(overdue_copy_pool)

    for i in range(min(OVERDUE_COUNT, len(overdue_copy_pool))):
        copy_id, book_id, item_type = overdue_copy_pool[i]
        checked_out_copy_ids.add(copy_id)
        user_id = pick_user()

        loan_period = LOAN_PERIODS.get(item_type, 21)

        # Checked out 30-60 days ago
        days_ago = random.randint(30, 60)
        checked_out_at = now - timedelta(days=days_ago)

        due_date = checked_out_at + timedelta(days=loan_period)
        # Due date should be in the past (overdue)
        if due_date > now:
            due_date = now - timedelta(days=random.randint(1, 10))

        loan_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "book_copy_id": copy_id,
            "checked_out_at": checked_out_at,
            "due_date": due_date,
            "returned_at": None,
            "renewed_count": 0,
            "status": "overdue",
            "created_at": checked_out_at,
        })

    # Batch insert all loans
    print(f"  Inserting {len(loan_records)} loans...")
    await db.execute(insert(Loan), loan_records)

    # Update book_copy status for active and overdue loans
    if checked_out_copy_ids:
        print(f"  Marking {len(checked_out_copy_ids)} copies as checked_out...")
        await db.execute(
            update(BookCopy)
            .where(BookCopy.id.in_(list(checked_out_copy_ids)))
            .values(status="checked_out")
        )

    await db.commit()
    print(f"  Seeded {len(loan_records)} loans ({RETURNED_COUNT} returned, {ACTIVE_COUNT} active, {OVERDUE_COUNT} overdue)")

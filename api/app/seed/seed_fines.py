"""Seed fines for late returns."""

import random
import uuid
from datetime import timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookCopy
from app.models.fine import Fine
from app.models.loan import Loan
from app.models.user import User

random.seed(42)

# Daily late fee rates by item type
DAILY_RATES = {
    "book": Decimal("0.25"),
    "ebook": Decimal("0.25"),
    "dvd": Decimal("1.00"),
    "audiobook": Decimal("0.50"),
    "magazine": Decimal("0.10"),
}

MAX_FINE = Decimal("25.00")

# Target: ~40 fines. Distribution: 24 pending, 10 paid, 6 waived
TARGET_PENDING = 24
TARGET_PAID = 10
TARGET_WAIVED = 6


async def seed_fines(db: AsyncSession) -> None:
    """Generate fines for late returns."""
    print("Seeding fines...")

    # Get admin users for waived_by
    admin_result = await db.execute(
        select(User.id).where(User.role == "admin")
    )
    admin_ids = [row[0] for row in admin_result.fetchall()]

    # Find returned loans where returned_at > due_date (late returns)
    late_loans_result = await db.execute(
        select(
            Loan.id,
            Loan.user_id,
            Loan.due_date,
            Loan.returned_at,
            Book.item_type,
        )
        .join(BookCopy, BookCopy.id == Loan.book_copy_id)
        .join(Book, Book.id == BookCopy.book_id)
        .where(Loan.status == "returned")
        .where(Loan.returned_at.isnot(None))
        .where(Loan.returned_at > Loan.due_date)
    )
    late_loans = late_loans_result.fetchall()

    print(f"  Found {len(late_loans)} late returns")

    if not late_loans:
        print("  No late returns found. Skipping fine generation.")
        await db.commit()
        return

    # Shuffle and take up to target total
    target_total = TARGET_PENDING + TARGET_PAID + TARGET_WAIVED
    late_loans_list = list(late_loans)
    random.shuffle(late_loans_list)
    selected_loans = late_loans_list[:target_total]

    fine_records = []
    for i, (loan_id, user_id, due_date, returned_at, item_type) in enumerate(selected_loans):
        days_overdue = (returned_at - due_date).days
        if days_overdue <= 0:
            continue

        daily_rate = DAILY_RATES.get(item_type, Decimal("0.25"))
        amount = min(daily_rate * days_overdue, MAX_FINE)

        # Determine fine status
        if i < TARGET_PENDING:
            status = "pending"
            paid_at = None
            waived_by = None
            waived_at = None
        elif i < TARGET_PENDING + TARGET_PAID:
            status = "paid"
            # Paid some time after the fine was created (1-30 days later)
            paid_at = returned_at + timedelta(days=random.randint(1, 30))
            waived_by = None
            waived_at = None
        else:
            status = "waived"
            paid_at = None
            waived_by = random.choice(admin_ids) if admin_ids else None
            waived_at = returned_at + timedelta(days=random.randint(1, 14))

        fine_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "loan_id": loan_id,
            "amount": amount,
            "reason": f"Late return - {days_overdue} day(s) overdue",
            "status": status,
            "paid_at": paid_at,
            "waived_by": waived_by,
            "waived_at": waived_at,
            "created_at": returned_at,
        })

    if fine_records:
        await db.execute(insert(Fine), fine_records)

    await db.commit()

    pending_count = sum(1 for f in fine_records if f["status"] == "pending")
    paid_count = sum(1 for f in fine_records if f["status"] == "paid")
    waived_count = sum(1 for f in fine_records if f["status"] == "waived")
    print(f"  Seeded {len(fine_records)} fines ({pending_count} pending, {paid_count} paid, {waived_count} waived)")

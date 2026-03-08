"""Seed mock reviews."""

import random
import uuid
from datetime import timedelta, timezone

from faker import Faker
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import BookCopy
from app.models.loan import Loan
from app.models.review import Review

fake = Faker()
Faker.seed(42)
random.seed(42)

TARGET_REVIEWS = 200

# Rating distribution: bell curve (5: 15%, 4: 35%, 3: 30%, 2: 15%, 1: 5%)
RATING_WEIGHTS = [5, 15, 30, 35, 15]  # indexes 0-4 map to ratings 1-5

# Short review templates for variety
REVIEW_TEMPLATES = [
    "Really enjoyed this one. {reason}",
    "Not what I expected, but {reason}",
    "A solid read. {reason}",
    "Couldn't put it down! {reason}",
    "A bit slow in places, but {reason}",
    "Absolutely brilliant. {reason}",
    "Good but not great. {reason}",
    "One of the best I've read this year. {reason}",
    "Interesting premise, {reason}",
    "Well-written and thought-provoking. {reason}",
]

REVIEW_REASONS = [
    "The writing style kept me hooked throughout.",
    "The characters felt very real and relatable.",
    "The plot twists were genuinely surprising.",
    "I learned a lot from this book.",
    "Perfect for a rainy weekend.",
    "The ending was satisfying.",
    "Would recommend to anyone who enjoys this genre.",
    "A great addition to my reading list.",
    "The pacing was just right.",
    "It made me think about things differently.",
    "The author has a wonderful voice.",
    "A page-turner from start to finish.",
]


def _generate_review_text() -> str | None:
    """Generate review text for 60% of reviews, None for 40%."""
    if random.random() > 0.60:
        return None

    # Mix of faker paragraphs and templates
    if random.random() < 0.5:
        template = random.choice(REVIEW_TEMPLATES)
        reason = random.choice(REVIEW_REASONS)
        return template.format(reason=reason)
    else:
        return fake.paragraph(nb_sentences=random.randint(2, 5))


async def seed_reviews(db: AsyncSession) -> None:
    """Generate 200 reviews for user+book combos with returned loans."""
    print("Seeding 200 reviews...")

    # Find all unique (user_id, book_id) pairs from returned loans
    eligible_result = await db.execute(
        select(Loan.user_id, BookCopy.book_id, Loan.returned_at)
        .join(BookCopy, BookCopy.id == Loan.book_copy_id)
        .where(Loan.status == "returned")
        .distinct(Loan.user_id, BookCopy.book_id)
    )
    eligible_pairs = eligible_result.fetchall()  # (user_id, book_id, returned_at)

    print(f"  Found {len(eligible_pairs)} eligible user-book pairs from returned loans")

    if not eligible_pairs:
        print("  No eligible pairs found. Skipping review generation.")
        await db.commit()
        return

    # Shuffle and select up to TARGET_REVIEWS
    eligible_list = list(eligible_pairs)
    random.shuffle(eligible_list)
    selected = eligible_list[:TARGET_REVIEWS]

    review_records = []
    seen_pairs = set()

    for user_id, book_id, returned_at in selected:
        pair = (user_id, book_id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        # Bell curve rating: 1-5
        rating = random.choices([1, 2, 3, 4, 5], weights=RATING_WEIGHTS, k=1)[0]
        review_text = _generate_review_text()

        # Review created 1-30 days after return
        created_at = returned_at + timedelta(days=random.randint(1, 30))

        review_records.append({
            "id": uuid.uuid4(),
            "user_id": user_id,
            "book_id": book_id,
            "rating": rating,
            "review_text": review_text,
            "created_at": created_at,
            "updated_at": created_at,
        })

    if review_records:
        await db.execute(insert(Review), review_records)

    await db.commit()

    with_text = sum(1 for r in review_records if r["review_text"])
    print(f"  Seeded {len(review_records)} reviews ({with_text} with text, {len(review_records) - with_text} rating only)")

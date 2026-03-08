"""Seed books and book copies from CSV data."""

import csv
import random
import uuid
from decimal import Decimal
from pathlib import Path

from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookCopy

# CSV path relative to api/ directory
CSV_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "books.csv"

# Genre quotas for diversity (first genre from categories column)
GENRE_QUOTAS = {
    "Fiction": 150,
    "Juvenile Fiction": 80,
    "Biography & Autobiography": 70,
    "History": 60,
    "Science Fiction": 100,
    "Fantasy": 100,
    "Literary Criticism": 40,
    "Philosophy": 40,
    "Comics & Graphic Novels": 40,
    "Religion": 30,
    "Drama": 30,
    "Poetry": 25,
    "Science": 30,
    "Business & Economics": 25,
    "Social Science": 20,
    "Cooking": 20,
    "Art": 20,
    "Psychology": 20,
    "Computers": 20,
    "Humor": 15,
    "Travel": 15,
}

# Well-known books to mark as staff picks (by partial title match)
STAFF_PICKS = {
    "1984": "Orwell's chilling masterpiece remains more relevant than ever.",
    "To Kill a Mockingbird": "A timeless exploration of justice and empathy in the American South.",
    "The Great Gatsby": "Fitzgerald's portrait of the American Dream at its most dazzling and hollow.",
    "Pride and Prejudice": "Austen's wit and wisdom at their finest — a perfect novel.",
    "The Catcher in the Rye": "Holden Caulfield's voice still resonates with every new generation.",
    "Brave New World": "A prophetic vision of a society numbed by pleasure.",
    "Fahrenheit 451": "Bradbury's love letter to books and the freedom to read.",
    "The Hobbit": "The adventure that launched a million fantasy epics.",
    "Dune": "Herbert's desert epic is science fiction at its most ambitious.",
    "Slaughterhouse-Five": "Vonnegut's anti-war masterpiece, unstuck in time.",
    "The Road": "McCarthy strips language to its bones in this devastating fable.",
    "Beloved": "Morrison's haunting meditation on memory and the scars of slavery.",
    "The Handmaid's Tale": "Atwood's dystopia feels uncomfortably close to reality.",
    "One Hundred Years of Solitude": "Magic realism at its most sweeping and unforgettable.",
    "Crime and Punishment": "Dostoevsky plumbs the darkest corners of conscience.",
    "The Lord of the Rings": "The gold standard for epic fantasy world-building.",
    "Sapiens": "Harari makes the whole sweep of human history feel fresh.",
    "Educated": "A memoir about the transformative power of learning.",
}

# Item type distribution: 90% book, 5% audiobook, 3% dvd, 2% ebook
ITEM_TYPES = (
    ["book"] * 90
    + ["audiobook"] * 5
    + ["dvd"] * 3
    + ["ebook"] * 2
)

# Condition distribution: 70% good, 15% new, 10% fair, 5% poor
CONDITIONS = (
    ["good"] * 70
    + ["new"] * 15
    + ["fair"] * 10
    + ["poor"] * 5
)


def _parse_csv() -> list[dict]:
    """Read and parse the books CSV, returning cleaned row dicts."""
    rows = []
    seen_isbn13 = set()

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("title") or "").strip()
            author = (row.get("authors") or "").strip()
            if not title or not author:
                continue

            description = (row.get("description") or "").strip() or None
            thumbnail = (row.get("thumbnail") or "").strip() or None
            if not description and not thumbnail:
                continue

            isbn13 = (row.get("isbn13") or "").strip() or None
            if isbn13:
                if isbn13 in seen_isbn13:
                    continue
                seen_isbn13.add(isbn13)

            subtitle = (row.get("subtitle") or "").strip()
            if subtitle:
                title = f"{title}: {subtitle}"

            categories_raw = (row.get("categories") or "").strip()
            genres_list = [g.strip() for g in categories_raw.split(";") if g.strip()] if categories_raw else []
            genre = genres_list[0] if genres_list else None

            avg_rating_str = (row.get("average_rating") or "").strip()
            avg_rating = Decimal(avg_rating_str) if avg_rating_str else Decimal("0.00")

            rating_count_str = (row.get("ratings_count") or "").strip()
            rating_count = int(rating_count_str) if rating_count_str else 0

            page_count_str = (row.get("num_pages") or "").strip()
            page_count = int(page_count_str) if page_count_str else None

            pub_year_str = (row.get("published_year") or "").strip()
            publication_year = int(pub_year_str) if pub_year_str else None

            isbn10 = (row.get("isbn10") or "").strip() or None

            rows.append({
                "title": title,
                "author": author,
                "isbn": isbn10,
                "isbn13": isbn13,
                "description": description,
                "genre": genre,
                "genres": genres_list,
                "cover_image_url": thumbnail,
                "avg_rating": avg_rating,
                "rating_count": rating_count,
                "page_count": page_count,
                "publication_year": publication_year,
            })

    return rows


def _select_diverse_books(all_rows: list[dict], target: int = 1000) -> list[dict]:
    """Select ~target books with genre diversity based on quotas."""
    # Group by genre
    by_genre: dict[str, list[dict]] = {}
    for row in all_rows:
        g = row.get("genre") or "Other"
        by_genre.setdefault(g, []).append(row)

    selected = []
    selected_isbn13s = set()

    # Fill quotas first
    for genre, quota in GENRE_QUOTAS.items():
        candidates = by_genre.get(genre, [])
        random.shuffle(candidates)
        count = 0
        for row in candidates:
            if count >= quota:
                break
            key = row.get("isbn13")
            if key and key in selected_isbn13s:
                continue
            selected.append(row)
            if key:
                selected_isbn13s.add(key)
            count += 1

    # Fill remaining from all genres
    remaining = target - len(selected)
    if remaining > 0:
        pool = [r for r in all_rows if (r.get("isbn13") or "") not in selected_isbn13s]
        random.shuffle(pool)
        for row in pool[:remaining]:
            selected.append(row)

    return selected[:target]


def _is_staff_pick(title: str) -> tuple[bool, str | None]:
    """Check if a book title matches a staff pick."""
    for pick_title, note in STAFF_PICKS.items():
        if pick_title.lower() in title.lower():
            return True, note
    return False, None


async def seed_books(db: AsyncSession) -> None:
    """Seed books and book copies from CSV."""
    random.seed(42)

    print("Parsing books CSV...")
    all_rows = _parse_csv()
    print(f"  Parsed {len(all_rows)} valid rows from CSV")

    books = _select_diverse_books(all_rows, target=1000)
    print(f"  Selected {len(books)} books with genre diversity")

    # Prepare book records
    book_records = []
    book_ids = []  # track UUIDs for copy generation
    staff_pick_count = 0

    for row in books:
        book_id = uuid.uuid4()
        book_ids.append(book_id)

        item_type = random.choice(ITEM_TYPES)
        is_pick, pick_note = _is_staff_pick(row["title"])
        if is_pick:
            staff_pick_count += 1

        book_records.append({
            "id": book_id,
            "title": row["title"],
            "author": row["author"],
            "isbn": row["isbn"],
            "isbn13": row["isbn13"],
            "description": row["description"],
            "genre": row["genre"],
            "genres": row["genres"],
            "item_type": item_type,
            "cover_image_url": row["cover_image_url"],
            "page_count": row["page_count"],
            "publication_year": row["publication_year"],
            "avg_rating": row["avg_rating"],
            "rating_count": row["rating_count"],
            "is_staff_pick": is_pick,
            "staff_pick_note": pick_note,
            "language": "en",
        })

    # Batch insert books
    print(f"Seeding {len(book_records)} books ({staff_pick_count} staff picks)...")
    await db.execute(insert(Book), book_records)
    await db.flush()

    # Prepare book copies
    copy_records = []
    copy_index = 1

    for i, book_rec in enumerate(book_records):
        avg = float(book_rec["avg_rating"])
        if avg >= 4.0:
            num_copies = 3
        elif avg >= 3.0:
            num_copies = 2
        else:
            num_copies = 1

        for c in range(1, num_copies + 1):
            barcode = f"PT-{copy_index:04d}-{c:02d}"
            copy_records.append({
                "id": uuid.uuid4(),
                "book_id": book_rec["id"],
                "barcode": barcode,
                "condition": random.choice(CONDITIONS),
                "status": "available",
            })
        copy_index += 1

    # Batch insert copies
    print(f"Seeding {len(copy_records)} book copies...")
    await db.execute(insert(BookCopy), copy_records)
    await db.commit()

    print(f"  Seeded {len(book_records)} books and {len(copy_records)} copies")

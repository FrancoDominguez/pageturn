"""Orchestrator: run all seed scripts in order.

Usage:
    python -m app.seed.run_seed
"""

import asyncio
import sys
import time
from pathlib import Path

# Load .env from project root (one level above api/)
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.seed.seed_books import seed_books
from app.seed.seed_fines import seed_fines
from app.seed.seed_loans import seed_loans
from app.seed.seed_reservations import seed_reservations
from app.seed.seed_reviews import seed_reviews
from app.seed.seed_users import seed_users

# Tables to truncate in dependency order (children first)
TABLES_TO_TRUNCATE = [
    "reviews",
    "fines",
    "reservations",
    "loans",
    "book_copies",
    "books",
    "api_keys",
    "users",
]


async def truncate_all(db) -> None:
    """Truncate all tables using CASCADE."""
    print("Truncating all tables...")
    for table in TABLES_TO_TRUNCATE:
        await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    await db.commit()
    print("  All tables truncated.")


async def main() -> None:
    """Run all seeders in order."""
    start = time.time()
    print("=" * 60)
    print("PageTurn Library - Database Seeder")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Truncate all tables
            await truncate_all(db)

            # Step 2: Seed in dependency order
            print()
            await seed_books(db)

            print()
            await seed_users(db)

            print()
            await seed_loans(db)

            print()
            await seed_reservations(db)

            print()
            await seed_fines(db)

            print()
            await seed_reviews(db)

        except Exception as e:
            print(f"\nERROR: Seeding failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"Seeding complete in {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

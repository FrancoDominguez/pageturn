"""Seed mock users."""

import random
import uuid
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

fake = Faker()
Faker.seed(42)
random.seed(42)

NUM_USERS = 50
NUM_ADMINS = 5
MAX_LOANS_CHOICES = [3, 5, 5, 5, 7, 10]


async def seed_users(db: AsyncSession) -> None:
    """Generate 50 mock users (5 admins + 45 regular users)."""
    print("Seeding 50 users...")

    now = datetime.now(timezone.utc)
    two_years_ago = now - timedelta(days=730)

    user_records = []
    seen_emails = set()

    for i in range(NUM_USERS):
        first_name = fake.first_name()
        last_name = fake.last_name()

        # Ensure unique email
        base_email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        email = base_email
        suffix = 1
        while email in seen_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{suffix}@example.com"
            suffix += 1
        seen_emails.add(email)

        role = "admin" if i < NUM_ADMINS else "user"
        clerk_id = f"mock_clerk_{i:03d}"

        # Random created_at over past 2 years
        days_ago = random.randint(0, 730)
        created_at = two_years_ago + timedelta(days=random.randint(0, 730))
        if created_at > now:
            created_at = now - timedelta(days=random.randint(1, 30))

        user_records.append({
            "id": uuid.uuid4(),
            "clerk_id": clerk_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "max_loans": random.choice(MAX_LOANS_CHOICES),
            "is_active": True,
            "created_at": created_at,
            "updated_at": created_at,
        })

    await db.execute(insert(User), user_records)
    await db.commit()

    print(f"  Seeded {len(user_records)} users ({NUM_ADMINS} admins, {NUM_USERS - NUM_ADMINS} regular)")

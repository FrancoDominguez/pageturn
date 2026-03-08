"""Promote a user to admin by email.
Usage: python scripts/promote_admin.py user@example.com
"""
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User


async def promote(email: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User {email} not found")
            return
        user.role = "admin"
        await db.commit()
        print(f"Promoted {email} to admin (id={user.id})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/promote_admin.py user@example.com")
        sys.exit(1)
    asyncio.run(promote(sys.argv[1]))

"""Generate an API key for a user (for MCP testing).
Usage: python scripts/generate_api_key.py user@example.com [--admin]
"""
import asyncio
import hashlib
import os
import secrets
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.api_key import ApiKey


async def generate(email: str, admin: bool = False):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User {email} not found")
            return

        scope = "adm" if (admin and user.role == "admin") else "usr"
        raw_key = secrets.token_hex(32)
        full_key = f"pt_{scope}_{raw_key}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_prefix = full_key[:10]

        api_key = ApiKey(
            user_id=user.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scope="admin" if scope == "adm" else "user",
            name="CLI Generated",
        )
        db.add(api_key)
        await db.commit()

        print(f"API Key generated for {email} (scope={scope}):")
        print(f"  {full_key}")
        print(f"  Save this key — you won't see it again.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_api_key.py user@example.com [--admin]")
        sys.exit(1)
    admin_flag = "--admin" in sys.argv
    asyncio.run(generate(sys.argv[1], admin_flag))

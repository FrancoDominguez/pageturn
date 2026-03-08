"""API key verification for the PageTurn MCP server.

Validates API keys against the database, checks scope/expiry,
and returns user context for tool execution.
"""

import hashlib
import os
from datetime import datetime, timezone

import asyncpg

DATABASE_URL = os.environ.get("DATABASE_URL", "")


async def _get_connection() -> asyncpg.Connection:
    """Create a single database connection."""
    return await asyncpg.connect(DATABASE_URL)


async def verify_api_key(
    key: str, required_scope: str | None = None
) -> dict:
    """Verify an API key and return the associated user context.

    Args:
        key: The raw API key string (e.g. "pt_usr_a1b2c3...").
        required_scope: If set, the key must have this scope (e.g. "admin").
                        A value of None means any valid scope is accepted.

    Returns:
        Dict with user_id, scope, role, email, first_name, last_name.

    Raises:
        ValueError: If the key is invalid, revoked, expired, or has
                    insufficient scope.
    """
    if not key:
        raise ValueError("API key is required")

    # Compute SHA-256 hash of the raw key
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    conn = await _get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT
                ak.id AS key_id,
                ak.user_id,
                ak.scope,
                ak.revoked_at,
                ak.expires_at,
                u.role,
                u.email,
                u.first_name,
                u.last_name
            FROM api_keys ak
            JOIN users u ON u.id = ak.user_id
            WHERE ak.key_hash = $1
            """,
            key_hash,
        )

        if row is None:
            raise ValueError("Invalid API key")

        # Check revocation
        if row["revoked_at"] is not None:
            raise ValueError("API key has been revoked")

        # Check expiry
        now = datetime.now(timezone.utc)
        if row["expires_at"] is not None and row["expires_at"] < now:
            raise ValueError("API key has expired")

        # Check scope
        key_scope = row["scope"]  # "user" or "admin"
        if required_scope == "admin" and key_scope != "admin":
            raise ValueError("Admin scope required")

        # Update last_used_at
        await conn.execute(
            "UPDATE api_keys SET last_used_at = $1 WHERE id = $2",
            now,
            row["key_id"],
        )

        return {
            "user_id": str(row["user_id"]),
            "scope": key_scope,
            "role": row["role"],
            "email": row["email"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
        }
    finally:
        await conn.close()

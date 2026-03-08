import hashlib
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import verify_clerk_jwt
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.user import User


async def _try_api_key_auth(token: str, db: AsyncSession) -> User | None:
    """Try to authenticate via API key. Returns User or None."""
    if not token.startswith("pt_"):
        return None

    key_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None

    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        return None

    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    if user and user.deleted_at is not None:
        return None
    return user


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and verify Clerk JWT or API key, return the user."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")

    token = authorization[7:]

    # Try API key auth first (fast check: starts with pt_)
    api_key_user = await _try_api_key_auth(token, db)
    if api_key_user:
        return api_key_user

    # Try Clerk JWT
    try:
        claims = await verify_clerk_jwt(token)
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

    clerk_id = claims.get("sub")
    if not clerk_id:
        raise HTTPException(401, "Invalid token claims")

    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")

    if user.deleted_at is not None:
        raise HTTPException(401, "Account deactivated")

    return user


async def get_current_user_optional(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None for unauthenticated requests."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]

    # Try API key first
    api_key_user = await _try_api_key_auth(token, db)
    if api_key_user:
        return api_key_user

    # Try Clerk JWT
    try:
        claims = await verify_clerk_jwt(token)
    except Exception:
        return None

    clerk_id = claims.get("sub")
    if not clerk_id:
        return None

    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if user and user.deleted_at is not None:
        return None
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require the current user to be an admin."""
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return user


async def get_api_key_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via API key only (for MCP servers)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")

    key = authorization[7:]
    user = await _try_api_key_auth(key, db)
    if not user:
        raise HTTPException(401, "Invalid API key")
    return user

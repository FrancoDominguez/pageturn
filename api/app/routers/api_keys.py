import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    ApiKeysListResponse,
)

router = APIRouter()


@router.post("/api/api-keys", response_model=ApiKeyCreatedResponse)
async def generate_api_key(
    data: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new API key. Returns plaintext once."""

    prefix = "pt_adm_" if user.role == "admin" else "pt_usr_"
    raw_key = prefix + secrets.token_hex(24)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:10]
    scope = "admin" if user.role == "admin" else "user"

    api_key = ApiKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scope=scope,
        name=data.name,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "api_key": {
            "id": str(api_key.id),
            "name": api_key.name,
            "key": raw_key,
            "key_prefix": key_prefix,
            "scope": scope,
            "created_at": api_key.created_at.isoformat(),
        },
        "warning": "Save this key -- you won't be able to see it again.",
    }


@router.get("/api/api-keys", response_model=ApiKeysListResponse)
async def list_api_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List API keys for the current user (prefix only)."""

    stmt = (
        select(ApiKey)
        .where(ApiKey.user_id == user.id)
        .order_by(ApiKey.created_at.desc())
    )
    result = await db.execute(stmt)
    keys = result.scalars().all()

    api_keys = []
    for k in keys:
        api_keys.append({
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "scope": k.scope,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat(),
            "is_active": k.revoked_at is None,
        })

    return {"api_keys": api_keys}


@router.delete("/api/api-keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""

    stmt = select(ApiKey).where(ApiKey.id == key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if api_key.user_id != user.id:
        raise HTTPException(status_code=403, detail="This is not your API key")

    if api_key.revoked_at is not None:
        raise HTTPException(status_code=409, detail="API key already revoked")

    api_key.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "API key revoked successfully"}

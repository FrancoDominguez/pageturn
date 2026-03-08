import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


async def _verify_webhook_signature(request: Request, body: bytes) -> bool:
    """Verify Clerk webhook signature using svix if webhook secret is configured."""
    if not settings.clerk_webhook_secret:
        # No secret configured; skip verification (dev mode)
        return True

    try:
        from svix.webhooks import Webhook

        wh = Webhook(settings.clerk_webhook_secret)
        headers = {
            "svix-id": request.headers.get("svix-id", ""),
            "svix-timestamp": request.headers.get("svix-timestamp", ""),
            "svix-signature": request.headers.get("svix-signature", ""),
        }
        wh.verify(body, headers)
        return True
    except Exception as e:
        logger.warning("Webhook signature verification failed: %s", e)
        return False


@router.post("/api/webhooks/clerk")
async def clerk_webhook(request: Request):
    """Receive Clerk webhook events (user.created, user.updated, user.deleted)."""

    body = await request.body()

    if not await _verify_webhook_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("type")
    data = payload.get("data", {})

    async with AsyncSessionLocal() as db:
        if event_type == "user.created":
            await _handle_user_created(db, data)
        elif event_type == "user.updated":
            await _handle_user_updated(db, data)
        elif event_type == "user.deleted":
            await _handle_user_deleted(db, data)
        else:
            logger.info("Ignoring unhandled Clerk event type: %s", event_type)

    return {"status": "ok"}


async def _handle_user_created(db: AsyncSession, data: dict) -> None:
    """Create a new user from Clerk user.created event."""
    clerk_id = data.get("id")
    if not clerk_id:
        return

    # Check if already exists
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    if result.scalar_one_or_none():
        return

    email_addresses = data.get("email_addresses", [])
    primary_email = ""
    primary_email_id = data.get("primary_email_address_id")
    for addr in email_addresses:
        if addr.get("id") == primary_email_id:
            primary_email = addr.get("email_address", "")
            break
    if not primary_email and email_addresses:
        primary_email = email_addresses[0].get("email_address", "")

    # Check role from public_metadata
    public_metadata = data.get("public_metadata", {})
    role = public_metadata.get("role", "user")
    if role not in ("admin", "user"):
        role = "user"

    user = User(
        clerk_id=clerk_id,
        email=primary_email,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        role=role,
    )
    db.add(user)
    await db.commit()
    logger.info("Created user %s from Clerk webhook", clerk_id)


async def _handle_user_updated(db: AsyncSession, data: dict) -> None:
    """Update user from Clerk user.updated event."""
    clerk_id = data.get("id")
    if not clerk_id:
        return

    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    email_addresses = data.get("email_addresses", [])
    primary_email_id = data.get("primary_email_address_id")
    for addr in email_addresses:
        if addr.get("id") == primary_email_id:
            user.email = addr.get("email_address", user.email)
            break

    if data.get("first_name") is not None:
        user.first_name = data["first_name"]
    if data.get("last_name") is not None:
        user.last_name = data["last_name"]

    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info("Updated user %s from Clerk webhook", clerk_id)


async def _handle_user_deleted(db: AsyncSession, data: dict) -> None:
    """Soft-delete user from Clerk user.deleted event."""
    clerk_id = data.get("id")
    if not clerk_id:
        return

    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    await db.commit()
    logger.info("Deactivated user %s from Clerk webhook", clerk_id)

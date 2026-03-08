import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.loan import Loan
from app.services.reservation_service import expire_reservations

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_cron_secret(request: Request) -> None:
    """Verify cron secret from authorization header or x-cron-secret header."""
    if not settings.cron_secret:
        # No secret configured; skip verification
        return

    secret = None

    # Check Authorization header (Bearer <secret>)
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        secret = auth[7:]

    # Fallback to x-cron-secret header
    if not secret:
        secret = request.headers.get("x-cron-secret")

    if secret != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Invalid cron secret")


@router.post("/api/cron/overdue")
async def mark_overdue_loans(request: Request):
    """Mark active loans past due_date as overdue."""
    _verify_cron_secret(request)

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        stmt = select(Loan).where(
            and_(
                Loan.status == "active",
                Loan.due_date < now,
            )
        )
        result = await db.execute(stmt)
        overdue_loans = result.scalars().all()

        count = 0
        for loan in overdue_loans:
            loan.status = "overdue"
            count += 1

        await db.commit()

    logger.info("Marked %d loans as overdue", count)
    return {"marked_overdue": count}


@router.post("/api/cron/expire-reservations")
async def expire_ready_reservations(request: Request):
    """Expire ready reservations past their expires_at."""
    _verify_cron_secret(request)

    async with AsyncSessionLocal() as db:
        count = await expire_reservations(db)

    logger.info("Expired %d reservations", count)
    return {"expired": count}

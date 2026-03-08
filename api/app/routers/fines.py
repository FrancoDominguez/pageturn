from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.fine import AdminFinesListResponse, FinesListResponse
from app.services import fine_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Member endpoints
# ---------------------------------------------------------------------------


@router.get("/api/fines", response_model=FinesListResponse)
async def get_my_fines(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await fine_service.get_user_fines(db, user.id)


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get("/api/admin/fines", response_model=AdminFinesListResponse)
async def get_admin_fines(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await fine_service.get_admin_fines(db, status=status, page=page, limit=limit)


@router.post("/api/admin/fines/{fine_id}/waive")
async def waive_fine(
    fine_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await fine_service.waive_fine(db, admin.id, fine_id)

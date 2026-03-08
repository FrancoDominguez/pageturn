from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.reservation import (
    ReservationsListResponse,
    ReserveRequest,
)
from app.services import reservation_service

router = APIRouter()


@router.post("/api/reservations")
async def reserve_book(
    data: ReserveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await reservation_service.reserve_book(db, user, data.book_id)


@router.get("/api/reservations", response_model=ReservationsListResponse)
async def get_my_reservations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reservations = await reservation_service.get_my_reservations(db, user.id)
    return {"reservations": reservations}


@router.delete("/api/reservations/{reservation_id}")
async def cancel_reservation(
    reservation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await reservation_service.cancel_reservation(db, user, reservation_id)

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.config import settings
from app.database import get_db
from app.models.book import Book, BookCopy
from app.models.fine import Fine
from app.models.loan import Loan
from app.models.reservation import Reservation
from app.models.review import Review
from app.models.user import User
from app.schemas.user import (
    AdminUserDetailResponse,
    AdminUsersListResponse,
    PromoteRequest,
    ReadingProfileResponse,
    StatsResponse,
    UserProfileResponse,
    UserUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Member endpoints
# ---------------------------------------------------------------------------


@router.get("/api/me", response_model=UserProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Active loan count
    loan_count_stmt = (
        select(func.count(Loan.id))
        .where(and_(Loan.user_id == user.id, Loan.status == "active"))
    )
    loan_count_result = await db.execute(loan_count_stmt)
    active_loan_count = loan_count_result.scalar_one()

    # Outstanding fines
    fines_stmt = (
        select(func.coalesce(func.sum(Fine.amount), Decimal("0.00")))
        .where(and_(Fine.user_id == user.id, Fine.status == "pending"))
    )
    fines_result = await db.execute(fines_stmt)
    outstanding_fines = float(fines_result.scalar_one())

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "max_loans": user.max_loans,
        "active_loan_count": active_loan_count,
        "outstanding_fines": outstanding_fines,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/api/me/reading-profile", response_model=ReadingProfileResponse)
async def get_reading_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate reading profile for AI recommendations."""

    # Total books read (returned loans)
    total_stmt = (
        select(func.count(Loan.id))
        .where(and_(Loan.user_id == user.id, Loan.status == "returned"))
    )
    total_result = await db.execute(total_stmt)
    total_books_read = total_result.scalar_one()

    # Favorite genres (top 3 by count from returned loans)
    genre_stmt = (
        select(Book.genre, func.count(Loan.id).label("cnt"))
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(
            and_(
                Loan.user_id == user.id,
                Loan.status == "returned",
                Book.genre.is_not(None),
            )
        )
        .group_by(Book.genre)
        .order_by(func.count(Loan.id).desc())
        .limit(3)
    )
    genre_result = await db.execute(genre_stmt)
    favorite_genres = [
        {"genre": row[0], "count": row[1]} for row in genre_result.all()
    ]

    # Favorite authors (top 3)
    author_stmt = (
        select(Book.author, func.count(Loan.id).label("cnt"))
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(and_(Loan.user_id == user.id, Loan.status == "returned"))
        .group_by(Book.author)
        .order_by(func.count(Loan.id).desc())
        .limit(3)
    )
    author_result = await db.execute(author_stmt)
    favorite_authors = [
        {"author": row[0], "count": row[1]} for row in author_result.all()
    ]

    # Average rating given
    avg_stmt = select(func.avg(Review.rating)).where(Review.user_id == user.id)
    avg_result = await db.execute(avg_stmt)
    avg_rating_raw = avg_result.scalar_one()
    avg_rating_given = round(float(avg_rating_raw), 2) if avg_rating_raw else None

    # Recent reads (last 5 returned loans)
    recent_stmt = (
        select(Book.title, Book.author, Book.genre, Book.cover_image_url)
        .join(BookCopy, Book.id == BookCopy.book_id)
        .join(Loan, BookCopy.id == Loan.book_copy_id)
        .where(and_(Loan.user_id == user.id, Loan.status == "returned"))
        .order_by(Loan.returned_at.desc())
        .limit(5)
    )
    recent_result = await db.execute(recent_stmt)
    recent_reads = [
        {
            "title": row[0],
            "author": row[1],
            "genre": row[2],
            "cover_image_url": row[3],
        }
        for row in recent_result.all()
    ]

    # Highly rated books (user rated 4 or 5 stars)
    high_stmt = (
        select(Book.title, Book.author, Book.genre, Review.rating)
        .join(Review, Book.id == Review.book_id)
        .where(and_(Review.user_id == user.id, Review.rating >= 4))
        .order_by(Review.rating.desc(), Review.created_at.desc())
    )
    high_result = await db.execute(high_stmt)
    highly_rated = [
        {
            "title": row[0],
            "author": row[1],
            "genre": row[2],
            "rating": row[3],
        }
        for row in high_result.all()
    ]

    return {
        "total_books_read": total_books_read,
        "favorite_genres": favorite_genres,
        "favorite_authors": favorite_authors,
        "avg_rating_given": avg_rating_given,
        "recent_reads": recent_reads,
        "highly_rated": highly_rated,
    }


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get("/api/admin/users", response_model=AdminUsersListResponse)
async def admin_list_users(
    q: str | None = Query(None),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = [User.deleted_at.is_(None)]
    if q:
        search = f"%{q}%"
        conditions.append(
            or_(
                User.email.ilike(search),
                User.first_name.ilike(search),
                User.last_name.ilike(search),
            )
        )
    if role:
        conditions.append(User.role == role)

    # Count
    count_stmt = select(func.count(User.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Active loans subquery
    loans_sub = (
        select(Loan.user_id, func.count(Loan.id).label("active_loans"))
        .where(Loan.status == "active")
        .group_by(Loan.user_id)
        .subquery()
    )

    # Outstanding fines subquery
    fines_sub = (
        select(Fine.user_id, func.sum(Fine.amount).label("outstanding_fines"))
        .where(Fine.status == "pending")
        .group_by(Fine.user_id)
        .subquery()
    )

    offset = (page - 1) * limit
    stmt = (
        select(
            User,
            func.coalesce(loans_sub.c.active_loans, 0).label("active_loans"),
            func.coalesce(fines_sub.c.outstanding_fines, Decimal("0.00")).label(
                "outstanding_fines"
            ),
        )
        .outerjoin(loans_sub, User.id == loans_sub.c.user_id)
        .outerjoin(fines_sub, User.id == fines_sub.c.user_id)
        .where(and_(*conditions))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    users = []
    for user_obj, active_loans, outstanding in rows:
        users.append({
            "id": user_obj.id,
            "email": user_obj.email,
            "first_name": user_obj.first_name,
            "last_name": user_obj.last_name,
            "role": user_obj.role,
            "active_loans": active_loans,
            "outstanding_fines": float(outstanding),
            "created_at": user_obj.created_at.isoformat(),
        })

    return {"users": users, "total": total, "page": page}


@router.get("/api/admin/users/{user_id}", response_model=AdminUserDetailResponse)
async def admin_user_detail(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Fetch user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = {
        "id": str(target_user.id),
        "email": target_user.email,
        "first_name": target_user.first_name,
        "last_name": target_user.last_name,
        "role": target_user.role,
        "max_loans": target_user.max_loans,
        "created_at": target_user.created_at.isoformat(),
    }

    # Active loans
    active_loans_stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(and_(Loan.user_id == user_id, Loan.status == "active"))
        .order_by(Loan.due_date.asc())
    )
    active_loans_result = await db.execute(active_loans_stmt)
    active_loans = [
        {
            "id": str(loan.id),
            "book_title": book.title,
            "due_date": loan.due_date.isoformat(),
            "status": loan.status,
        }
        for loan, _copy, book in active_loans_result.all()
    ]

    # Loan history (last 10)
    history_stmt = (
        select(Loan, BookCopy, Book)
        .join(BookCopy, Loan.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(and_(Loan.user_id == user_id, Loan.status == "returned"))
        .order_by(Loan.returned_at.desc())
        .limit(10)
    )
    history_result = await db.execute(history_stmt)
    loan_history = [
        {
            "id": str(loan.id),
            "book_title": book.title,
            "returned_at": loan.returned_at.isoformat() if loan.returned_at else None,
        }
        for loan, _copy, book in history_result.all()
    ]

    # Reservations
    res_stmt = (
        select(Reservation, Book)
        .join(Book, Reservation.book_id == Book.id)
        .where(
            and_(
                Reservation.user_id == user_id,
                Reservation.status.in_(["pending", "ready"]),
            )
        )
    )
    res_result = await db.execute(res_stmt)
    reservations = [
        {
            "id": str(r.id),
            "book_title": book.title,
            "status": r.status,
            "queue_position": r.queue_position,
        }
        for r, book in res_result.all()
    ]

    # Fines
    fines_stmt = (
        select(Fine)
        .where(Fine.user_id == user_id)
        .order_by(Fine.created_at.desc())
    )
    fines_result = await db.execute(fines_stmt)
    fines = [
        {
            "id": str(f.id),
            "amount": float(f.amount),
            "reason": f.reason,
            "status": f.status,
        }
        for f in fines_result.scalars().all()
    ]

    # Reviews
    reviews_stmt = (
        select(Review, Book)
        .join(Book, Review.book_id == Book.id)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    reviews_result = await db.execute(reviews_stmt)
    reviews = [
        {
            "id": str(rev.id),
            "book_title": book.title,
            "rating": rev.rating,
        }
        for rev, book in reviews_result.all()
    ]

    return {
        "user": user_dict,
        "active_loans": active_loans,
        "loan_history": loan_history,
        "reservations": reservations,
        "fines": fines,
        "reviews": reviews,
    }


@router.put("/api/admin/users/{user_id}")
async def admin_update_user(
    user_id: UUID,
    data: UserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target_user, field, value)

    target_user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(target_user)

    return {
        "id": target_user.id,
        "email": target_user.email,
        "role": target_user.role,
        "max_loans": target_user.max_loans,
        "message": "User updated successfully",
    }


@router.post("/api/admin/users/{user_id}/promote")
async def promote_user(
    user_id: UUID,
    data: PromoteRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if data.role not in ("admin", "user"):
        raise HTTPException(status_code=422, detail="Role must be 'admin' or 'user'")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = target_user.role
    target_user.role = data.role
    target_user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(target_user)

    # Sync role to Clerk via Backend API
    try:
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"https://api.clerk.com/v1/users/{target_user.clerk_id}",
                headers={
                    "Authorization": f"Bearer {settings.clerk_secret_key}",
                    "Content-Type": "application/json",
                },
                json={"public_metadata": {"role": data.role}},
            )
    except Exception:
        # Log but don't fail the request; DB is source of truth
        pass

    return {
        "id": target_user.id,
        "email": target_user.email,
        "old_role": old_role,
        "new_role": target_user.role,
        "message": f"User {'promoted to admin' if data.role == 'admin' else 'demoted to user'}",
    }


@router.get("/api/admin/stats", response_model=StatsResponse)
async def admin_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    # Total books
    total_books_stmt = select(func.count(Book.id))
    total_books = (await db.execute(total_books_stmt)).scalar_one()

    # Total copies
    total_copies_stmt = select(func.count(BookCopy.id))
    total_copies = (await db.execute(total_copies_stmt)).scalar_one()

    # Active loans
    active_loans_stmt = select(func.count(Loan.id)).where(Loan.status == "active")
    active_loans = (await db.execute(active_loans_stmt)).scalar_one()

    # Overdue loans (active loans past due_date)
    overdue_stmt = select(func.count(Loan.id)).where(
        and_(Loan.status == "active", Loan.due_date < now)
    )
    overdue_loans = (await db.execute(overdue_stmt)).scalar_one()

    # Total users
    total_users_stmt = select(func.count(User.id)).where(User.deleted_at.is_(None))
    total_users = (await db.execute(total_users_stmt)).scalar_one()

    # Total outstanding fines
    fines_stmt = select(
        func.coalesce(func.sum(Fine.amount), Decimal("0.00"))
    ).where(Fine.status == "pending")
    total_fines = float((await db.execute(fines_stmt)).scalar_one())

    # Loans today
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(
        tzinfo=now.tzinfo
    )
    loans_today_stmt = select(func.count(Loan.id)).where(
        Loan.checked_out_at >= today_start
    )
    loans_today = (await db.execute(loans_today_stmt)).scalar_one()

    # Returns today
    returns_today_stmt = select(func.count(Loan.id)).where(
        and_(Loan.returned_at >= today_start, Loan.status == "returned")
    )
    returns_today = (await db.execute(returns_today_stmt)).scalar_one()

    return {
        "total_books": total_books,
        "total_copies": total_copies,
        "active_loans": active_loans,
        "overdue_loans": overdue_loans,
        "total_users": total_users,
        "total_fines_outstanding": total_fines,
        "loans_today": loans_today,
        "returns_today": returns_today,
    }

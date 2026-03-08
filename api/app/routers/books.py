from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_optional, require_admin
from app.database import get_db
from app.models.review import Review
from app.models.user import User
from app.schemas.book import (
    BookCreate,
    BookDetailResponse,
    BooksListResponse,
    BookUpdate,
    CopyCreate,
    CopyUpdate,
)
from app.schemas.review import BookReviewsResponse
from app.services import book_service, search_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------


@router.get("/api/books", response_model=BooksListResponse)
async def search_books(
    q: str | None = Query(None),
    genre: str | None = Query(None),
    author: str | None = Query(None),
    item_type: str | None = Query(None),
    available: bool = Query(False),
    staff_picks: bool = Query(False),
    sort: str = Query("relevance"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.search_books(
        db,
        query=q,
        genre=genre,
        author=author,
        item_type=item_type,
        available=available,
        staff_picks=staff_picks,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.get("/api/books/{book_id}", response_model=BookDetailResponse)
async def get_book_detail(
    book_id: UUID,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.id if user else None
    return await book_service.get_book_detail(db, book_id, user_id=user_id)


@router.get("/api/books/{book_id}/reviews", response_model=BookReviewsResponse)
async def get_book_reviews(
    book_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("newest"),
    db: AsyncSession = Depends(get_db),
):
    """Get reviews for a book with rating distribution (inline query)."""

    # Rating distribution: count per star (1-5)
    dist_stmt = (
        select(Review.rating, func.count(Review.id))
        .where(Review.book_id == book_id)
        .group_by(Review.rating)
    )
    dist_result = await db.execute(dist_stmt)
    dist_rows = dist_result.all()

    rating_distribution = {str(i): 0 for i in range(1, 6)}
    total_rating_sum = 0
    rating_count = 0
    for rating_val, cnt in dist_rows:
        rating_distribution[str(rating_val)] = cnt
        total_rating_sum += rating_val * cnt
        rating_count += cnt

    avg_rating = round(total_rating_sum / rating_count, 2) if rating_count > 0 else 0.0

    # Total count for pagination
    total = rating_count

    # Paginated reviews joined with users
    order = Review.created_at.desc()
    if sort == "oldest":
        order = Review.created_at.asc()
    elif sort == "highest":
        order = Review.rating.desc()
    elif sort == "lowest":
        order = Review.rating.asc()

    offset = (page - 1) * limit
    reviews_stmt = (
        select(Review, User)
        .join(User, Review.user_id == User.id)
        .where(Review.book_id == book_id)
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    reviews_result = await db.execute(reviews_stmt)
    rows = reviews_result.all()

    reviews = []
    for review, user in rows:
        first = user.first_name or ""
        last = user.last_name or ""
        display_name = f"{first} {last}".strip() or user.email.split("@")[0]
        initial = display_name[0].upper() if display_name else "?"

        reviews.append({
            "id": review.id,
            "user_name": display_name,
            "user_initial": initial,
            "rating": review.rating,
            "review_text": review.review_text,
            "created_at": review.created_at.isoformat(),
        })

    return {
        "reviews": reviews,
        "avg_rating": avg_rating,
        "rating_count": rating_count,
        "rating_distribution": rating_distribution,
        "total": total,
        "page": page,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------


@router.post("/api/admin/books")
async def create_book(
    data: BookCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.create_book(db, data)


@router.put("/api/admin/books/{book_id}")
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.update_book(db, book_id, data)


@router.delete("/api/admin/books/{book_id}")
async def delete_book(
    book_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.delete_book(db, book_id)


@router.post("/api/admin/books/{book_id}/copies")
async def add_copies(
    book_id: UUID,
    data: CopyCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.add_copies(db, book_id, count=data.count, condition=data.condition)


@router.put("/api/admin/book-copies/{copy_id}")
async def update_copy(
    copy_id: UUID,
    data: CopyUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.update_copy(db, copy_id, status=data.status, condition=data.condition)

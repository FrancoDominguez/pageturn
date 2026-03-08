from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.book import Book
from app.models.review import Review
from app.models.user import User
from app.schemas.review import MyReviewResponse, ReviewCreate

router = APIRouter()


@router.post("/api/reviews")
async def create_or_update_review(
    data: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a review (upsert by user_id + book_id)."""

    # Verify book exists
    book_stmt = select(Book).where(Book.id == data.book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")

    # Check if review already exists
    existing_stmt = select(Review).where(
        and_(Review.user_id == user.id, Review.book_id == data.book_id)
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.rating = data.rating
        existing.review_text = data.review_text
        await db.commit()
        await db.refresh(existing)
        review = existing
        action = "updated"
    else:
        review = Review(
            user_id=user.id,
            book_id=data.book_id,
            rating=data.rating,
            review_text=data.review_text,
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        action = "created"

    # Update book avg_rating and rating_count
    from sqlalchemy import func

    stats_stmt = select(
        func.avg(Review.rating), func.count(Review.id)
    ).where(Review.book_id == data.book_id)
    stats_result = await db.execute(stats_stmt)
    avg, count = stats_result.one()
    book.avg_rating = round(avg, 2) if avg else 0
    book.rating_count = count
    await db.commit()

    return {
        "id": review.id,
        "book_id": review.book_id,
        "rating": review.rating,
        "review_text": review.review_text,
        "created_at": review.created_at.isoformat(),
        "action": action,
    }


@router.get("/api/reviews/mine")
async def get_my_reviews(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews by the current user."""

    stmt = (
        select(Review, Book)
        .join(Book, Review.book_id == Book.id)
        .where(Review.user_id == user.id)
        .order_by(Review.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    reviews = []
    for review, book in rows:
        reviews.append({
            "id": review.id,
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "cover_image_url": book.cover_image_url,
            },
            "rating": review.rating,
            "review_text": review.review_text,
            "created_at": review.created_at.isoformat(),
        })

    return {"reviews": reviews}


@router.delete("/api/reviews/{review_id}")
async def delete_review(
    review_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a review owned by the current user."""

    stmt = select(Review).where(Review.id == review_id)
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != user.id:
        raise HTTPException(status_code=403, detail="This is not your review")

    book_id = review.book_id
    await db.delete(review)
    await db.commit()

    # Recalculate book rating
    from sqlalchemy import func

    book_stmt = select(Book).where(Book.id == book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    if book:
        stats_stmt = select(
            func.avg(Review.rating), func.count(Review.id)
        ).where(Review.book_id == book_id)
        stats_result = await db.execute(stats_stmt)
        avg, count = stats_result.one()
        book.avg_rating = round(avg, 2) if avg else 0
        book.rating_count = count
        await db.commit()

    return {"message": "Review deleted successfully"}

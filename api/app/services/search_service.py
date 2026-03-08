import math

from sqlalchemy import and_, case, func, literal, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book, BookCopy


async def search_books(
    db: AsyncSession,
    query: str | None = None,
    genre: str | None = None,
    author: str | None = None,
    item_type: str | None = None,
    available: bool = False,
    staff_picks: bool = False,
    sort: str = "relevance",
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Search books with full-text search, filters, and pagination."""

    # Subquery: count total and available copies per book
    copies_sub = (
        select(
            BookCopy.book_id,
            func.count(BookCopy.id).label("total_copies"),
            func.count(
                case((BookCopy.status == "available", BookCopy.id))
            ).label("available_copies"),
        )
        .group_by(BookCopy.book_id)
        .subquery()
    )

    # Base query joining books with copy counts
    stmt = (
        select(
            Book,
            func.coalesce(copies_sub.c.total_copies, 0).label("total_copies"),
            func.coalesce(copies_sub.c.available_copies, 0).label("available_copies"),
        )
        .outerjoin(copies_sub, Book.id == copies_sub.c.book_id)
    )

    rank_column = None

    # Full-text search
    if query:
        ts_query = func.plainto_tsquery("english", query)
        rank_column = func.ts_rank(Book.search_vector, ts_query)
        stmt = stmt.add_columns(rank_column.label("rank"))
        stmt = stmt.where(Book.search_vector.op("@@")(ts_query))
    else:
        stmt = stmt.add_columns(literal(0).label("rank"))

    # Filters
    if genre:
        stmt = stmt.where(Book.genre == genre)
    if author:
        stmt = stmt.where(Book.author.ilike(f"%{author}%"))
    if item_type:
        stmt = stmt.where(Book.item_type == item_type)
    if staff_picks:
        stmt = stmt.where(Book.is_staff_pick.is_(True))
    if available:
        stmt = stmt.where(func.coalesce(copies_sub.c.available_copies, 0) > 0)

    # Execute count before applying sort/pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # If FTS query returned zero results, fall back to ILIKE on title/author
    if query and total == 0:
        stmt = (
            select(
                Book,
                func.coalesce(copies_sub.c.total_copies, 0).label("total_copies"),
                func.coalesce(copies_sub.c.available_copies, 0).label("available_copies"),
                literal(0).label("rank"),
            )
            .outerjoin(copies_sub, Book.id == copies_sub.c.book_id)
            .where(
                or_(
                    Book.title.ilike(f"%{query}%"),
                    Book.author.ilike(f"%{query}%"),
                )
            )
        )
        # Re-apply filters
        if genre:
            stmt = stmt.where(Book.genre == genre)
        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))
        if item_type:
            stmt = stmt.where(Book.item_type == item_type)
        if staff_picks:
            stmt = stmt.where(Book.is_staff_pick.is_(True))
        if available:
            stmt = stmt.where(func.coalesce(copies_sub.c.available_copies, 0) > 0)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

    # Sorting
    if sort == "title_asc":
        stmt = stmt.order_by(Book.title.asc())
    elif sort == "title_desc":
        stmt = stmt.order_by(Book.title.desc())
    elif sort == "rating_desc":
        stmt = stmt.order_by(Book.avg_rating.desc())
    elif sort == "year_desc":
        stmt = stmt.order_by(Book.publication_year.desc().nulls_last())
    elif sort == "relevance":
        if query:
            # ts_rank ordering for FTS queries
            ts_query = func.plainto_tsquery("english", query)
            stmt = stmt.order_by(func.ts_rank(Book.search_vector, ts_query).desc())
        else:
            stmt = stmt.order_by(Book.avg_rating.desc())
    else:
        stmt = stmt.order_by(Book.avg_rating.desc())

    # Pagination
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    books = []
    for row in rows:
        book = row[0]
        t_copies = row[1]
        a_copies = row[2]
        books.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "genre": book.genre,
            "item_type": book.item_type,
            "cover_image_url": book.cover_image_url,
            "avg_rating": float(book.avg_rating) if book.avg_rating else 0.0,
            "rating_count": book.rating_count,
            "publication_year": book.publication_year,
            "is_staff_pick": book.is_staff_pick,
            "staff_pick_note": book.staff_pick_note,
            "available_copies": a_copies,
            "total_copies": t_copies,
        })

    pages = math.ceil(total / limit) if limit > 0 else 0

    return {
        "books": books,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }

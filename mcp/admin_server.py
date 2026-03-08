"""PageTurn Admin MCP Server.

Exposes all user tools plus admin-level operations: book CRUD,
inventory management, user management, fine waiving, and reporting.
"""

import os

from mcp.server.fastmcp import FastMCP

# User tool implementations
from tools.search import search_books as _search_books
from tools.books_detail import get_book_details as _get_book_details
from tools.loans import (
    get_my_loans as _get_my_loans,
    get_loan_history as _get_loan_history,
    checkout_book as _checkout_book,
    renew_loan as _renew_loan,
)
from tools.reservations import (
    get_my_reservations as _get_my_reservations,
    cancel_reservation as _cancel_reservation,
)
from tools.reviews import (
    get_my_reviews as _get_my_reviews,
    get_book_reviews as _get_book_reviews,
    create_review as _create_review,
)
from tools.fines import (
    get_my_fines as _get_my_fines,
    waive_fine as _waive_fine,
)
from tools.reading_profile import get_reading_profile as _get_reading_profile

# Admin tool implementations
from tools.books_admin import (
    create_book as _create_book,
    update_book as _update_book,
    delete_book as _delete_book,
    add_copies as _add_copies,
)
from tools.users import (
    lookup_user as _lookup_user,
    get_user_details as _get_user_details,
)
from tools.stats import (
    get_overdue_report as _get_overdue_report,
    get_stats as _get_stats,
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:3000")

mcp = FastMCP(
    "PageTurn Admin",
    instructions=(
        "You are the PageTurn Library admin assistant. You have access to all "
        "member tools (search, loans, reservations, reviews, fines, reading "
        "profile) plus admin operations: book CRUD, inventory management, "
        "user management, fine waiving, return processing, and reporting. "
        "Use admin tools responsibly — they modify library data."
    ),
)


# ---------------------------------------------------------------------------
# Helper to extract API key from the MCP request context
# ---------------------------------------------------------------------------

def _get_api_key_from_context(ctx) -> str:
    """Extract the API key from the MCP request context."""
    try:
        request = ctx.request_context.request
        if hasattr(request.state, "api_key"):
            return request.state.api_key
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
    except Exception:
        pass
    raise ValueError("No API key found in request context")


# ---------------------------------------------------------------------------
# User tools (same as user_server.py)
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_books(
    ctx,
    query: str,
    genre: str | None = None,
    author: str | None = None,
    item_type: str | None = None,
    limit: int = 10,
) -> str:
    """Search the library catalogue by title, author, genre, or keyword.

    Args:
        query: Search text (title, author, keyword).
        genre: Filter by genre (e.g., "Fiction", "Science Fiction").
        author: Filter by author name.
        item_type: Filter by type: book, audiobook, dvd, ebook, magazine.
        limit: Max results (default 10, max 50).
    """
    api_key = _get_api_key_from_context(ctx)
    return await _search_books(
        API_BASE_URL, api_key, query, genre, author, item_type, limit
    )


@mcp.tool()
async def get_book_details(ctx, book_id: str) -> str:
    """Get full information about a specific book including availability and reviews.

    Args:
        book_id: UUID of the book.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _get_book_details(API_BASE_URL, api_key, book_id)


@mcp.tool()
async def get_my_loans(ctx) -> str:
    """List your current active loans with due dates and renewal eligibility."""
    api_key = _get_api_key_from_context(ctx)
    return await _get_my_loans(API_BASE_URL, api_key)


@mcp.tool()
async def get_loan_history(
    ctx, limit: int = 20, offset: int = 0
) -> str:
    """List your past loans (returned books).

    Args:
        limit: Max results (default 20).
        offset: Skip N results for pagination.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _get_loan_history(API_BASE_URL, api_key, limit, offset)


@mcp.tool()
async def checkout_book(ctx, book_id: str) -> str:
    """Check out a book or join the waitlist if all copies are checked out.

    Args:
        book_id: UUID of the book to check out.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _checkout_book(API_BASE_URL, api_key, book_id)


@mcp.tool()
async def renew_loan(ctx, loan_id: str) -> str:
    """Renew an active loan to extend the due date.

    Args:
        loan_id: UUID of the loan to renew.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _renew_loan(API_BASE_URL, api_key, loan_id)


@mcp.tool()
async def get_my_reservations(ctx) -> str:
    """List your active reservations with status and queue position."""
    api_key = _get_api_key_from_context(ctx)
    return await _get_my_reservations(API_BASE_URL, api_key)


@mcp.tool()
async def cancel_reservation(ctx, reservation_id: str) -> str:
    """Cancel a pending or ready reservation.

    Args:
        reservation_id: UUID of the reservation to cancel.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _cancel_reservation(API_BASE_URL, api_key, reservation_id)


@mcp.tool()
async def get_my_fines(ctx) -> str:
    """View your outstanding fines and dues with total balance."""
    api_key = _get_api_key_from_context(ctx)
    return await _get_my_fines(API_BASE_URL, api_key)


@mcp.tool()
async def get_my_reviews(ctx) -> str:
    """Get all reviews you have written. Useful for understanding your reading preferences."""
    api_key = _get_api_key_from_context(ctx)
    return await _get_my_reviews(API_BASE_URL, api_key)


@mcp.tool()
async def get_book_reviews(ctx, book_id: str) -> str:
    """Get public reviews for a specific book with average rating.

    Args:
        book_id: UUID of the book.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _get_book_reviews(API_BASE_URL, api_key, book_id)


@mcp.tool()
async def create_review(
    ctx, book_id: str, rating: int, review_text: str | None = None
) -> str:
    """Rate and optionally review a book you have borrowed.

    Args:
        book_id: UUID of the book.
        rating: 1-5 star rating.
        review_text: Optional written review.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _create_review(
        API_BASE_URL, api_key, book_id, rating, review_text
    )


@mcp.tool()
async def get_reading_profile(ctx) -> str:
    """Get your aggregated reading profile for personalized recommendations.

    Returns total books read, favorite genres and authors, average rating,
    recent reads, and highly rated books.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _get_reading_profile(API_BASE_URL, api_key)


# ---------------------------------------------------------------------------
# Admin tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_book(
    ctx,
    title: str,
    author: str,
    isbn: str | None = None,
    isbn13: str | None = None,
    description: str | None = None,
    genre: str | None = None,
    genres: list[str] | None = None,
    item_type: str | None = None,
    cover_image_url: str | None = None,
    page_count: int | None = None,
    publication_year: int | None = None,
    publisher: str | None = None,
    copies: int | None = None,
) -> str:
    """Add a new book to the catalogue.

    Args:
        title: Book title.
        author: Author name.
        isbn: ISBN-10 (optional).
        isbn13: ISBN-13 (optional).
        description: Book description (optional).
        genre: Primary genre (optional).
        genres: All genres as a list (optional).
        item_type: book, audiobook, dvd, ebook, or magazine (optional).
        cover_image_url: URL to cover image (optional).
        page_count: Number of pages (optional).
        publication_year: Year published (optional).
        publisher: Publisher name (optional).
        copies: Number of copies to create, default 1 (optional).
    """
    api_key = _get_api_key_from_context(ctx)
    return await _create_book(
        API_BASE_URL, api_key, title, author, isbn, isbn13, description,
        genre, genres, item_type, cover_image_url, page_count,
        publication_year, publisher, copies,
    )


@mcp.tool()
async def update_book(
    ctx,
    book_id: str,
    title: str | None = None,
    author: str | None = None,
    isbn: str | None = None,
    isbn13: str | None = None,
    description: str | None = None,
    genre: str | None = None,
    genres: list[str] | None = None,
    item_type: str | None = None,
    cover_image_url: str | None = None,
    page_count: int | None = None,
    publication_year: int | None = None,
    publisher: str | None = None,
) -> str:
    """Edit an existing book's metadata.

    Args:
        book_id: UUID of the book to update.
        title: Updated title (optional).
        author: Updated author (optional).
        isbn: Updated ISBN-10 (optional).
        isbn13: Updated ISBN-13 (optional).
        description: Updated description (optional).
        genre: Updated primary genre (optional).
        genres: Updated genre list (optional).
        item_type: Updated item type (optional).
        cover_image_url: Updated cover URL (optional).
        page_count: Updated page count (optional).
        publication_year: Updated publication year (optional).
        publisher: Updated publisher (optional).
    """
    api_key = _get_api_key_from_context(ctx)
    return await _update_book(
        API_BASE_URL, api_key, book_id, title, author, isbn, isbn13,
        description, genre, genres, item_type, cover_image_url,
        page_count, publication_year, publisher,
    )


@mcp.tool()
async def delete_book(ctx, book_id: str) -> str:
    """Remove a book from the catalogue. Fails if copies are currently on loan.

    Args:
        book_id: UUID of the book to delete.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _delete_book(API_BASE_URL, api_key, book_id)


@mcp.tool()
async def add_copies(
    ctx, book_id: str, count: int, condition: str | None = None
) -> str:
    """Add copies to an existing book to increase inventory.

    Args:
        book_id: UUID of the book.
        count: Number of copies to add.
        condition: Condition of new copies: new, good, fair, poor (default "new").
    """
    api_key = _get_api_key_from_context(ctx)
    return await _add_copies(
        API_BASE_URL, api_key, book_id, count, condition
    )


@mcp.tool()
async def lookup_user(ctx, query: str) -> str:
    """Search for a user by name or email.

    Args:
        query: Name or email to search.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _lookup_user(API_BASE_URL, api_key, query)


@mcp.tool()
async def get_user_details(ctx, user_id: str) -> str:
    """Get full profile of a user including loans, fines, and reviews.

    Args:
        user_id: UUID of the user.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _get_user_details(API_BASE_URL, api_key, user_id)


@mcp.tool()
async def process_return(ctx, loan_id: str) -> str:
    """Mark a book as returned. Calculates fines if overdue.

    Args:
        loan_id: UUID of the loan to mark as returned.
    """
    import httpx

    api_key = _get_api_key_from_context(ctx)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE_URL}/api/admin/loans/{loan_id}/return",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def waive_fine(ctx, fine_id: str) -> str:
    """Waive a fine for a user.

    Args:
        fine_id: UUID of the fine to waive.
    """
    api_key = _get_api_key_from_context(ctx)
    return await _waive_fine(API_BASE_URL, api_key, fine_id)


@mcp.tool()
async def get_overdue_report(ctx) -> str:
    """Get a list of all overdue loans with user and fine info."""
    api_key = _get_api_key_from_context(ctx)
    return await _get_overdue_report(API_BASE_URL, api_key)


@mcp.tool()
async def get_stats(ctx) -> str:
    """Get library-wide statistics: books, copies, loans, users, fines."""
    api_key = _get_api_key_from_context(ctx)
    return await _get_stats(API_BASE_URL, api_key)

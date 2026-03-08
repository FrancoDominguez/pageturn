"""PageTurn User MCP Server.

Exposes library tools for authenticated members: search, loans,
reservations, reviews, fines, and reading profile.
"""

import os

from mcp.server.fastmcp import FastMCP

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
from tools.fines import get_my_fines as _get_my_fines
from tools.reading_profile import get_reading_profile as _get_reading_profile

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:3000")

mcp = FastMCP(
    "PageTurn Library",
    instructions=(
        "You are the PageTurn Library assistant. Help users search for books, "
        "manage their loans, reservations, reviews, and fines. You can also "
        "build personalized book recommendations by combining the user's "
        "reading profile, loan history, reviews, and catalogue search."
    ),
)


# ---------------------------------------------------------------------------
# Helper to extract API key from the MCP request context
# ---------------------------------------------------------------------------

def _get_api_key_from_context(ctx) -> str:
    """Extract the API key from the MCP request context.

    The key is passed by the auth middleware and stored in the
    request state as 'api_key'. Falls back to the Authorization header.
    """
    # The auth middleware stores the raw key in request state
    try:
        request = ctx.request_context.request
        # Try request state first (set by our auth middleware)
        if hasattr(request.state, "api_key"):
            return request.state.api_key
        # Fall back to Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
    except Exception:
        pass
    raise ValueError("No API key found in request context")


# ---------------------------------------------------------------------------
# User tools
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

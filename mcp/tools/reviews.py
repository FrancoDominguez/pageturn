"""Review tools for the PageTurn MCP server."""

import httpx


async def get_my_reviews(
    api_base_url: str,
    api_key: str,
) -> str:
    """Get all reviews the user has written.

    Useful for understanding reading preferences and history.

    Returns:
        JSON string with reviews including book info, ratings, and text.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/reviews/mine",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def get_book_reviews(
    api_base_url: str,
    api_key: str,
    book_id: str,
) -> str:
    """Get public reviews for a specific book.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        book_id: UUID of the book.

    Returns:
        JSON string with reviews from all users, average rating,
        and rating distribution.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/books/{book_id}/reviews",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def create_review(
    api_base_url: str,
    api_key: str,
    book_id: str,
    rating: int,
    review_text: str | None = None,
) -> str:
    """Rate and optionally review a book the user has borrowed.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        book_id: UUID of the book.
        rating: 1-5 star rating.
        review_text: Optional written review.

    Returns:
        JSON string confirming the created/updated review.
    """
    body: dict = {"book_id": book_id, "rating": rating}
    if review_text is not None:
        body["review_text"] = review_text

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{api_base_url}/api/reviews",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

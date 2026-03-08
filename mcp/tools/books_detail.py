"""Book detail tools for the PageTurn MCP server."""

import httpx


async def get_book_details(
    api_base_url: str,
    api_key: str,
    book_id: str,
) -> str:
    """Get full information about a specific book.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        book_id: UUID of the book.

    Returns:
        JSON string with complete book metadata, availability status,
        copy count, earliest return date, and user's loan/reservation status.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/books/{book_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

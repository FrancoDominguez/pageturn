"""Search tools for the PageTurn MCP server."""

import httpx


async def search_books(
    api_base_url: str,
    api_key: str,
    query: str,
    genre: str | None = None,
    author: str | None = None,
    item_type: str | None = None,
    limit: int = 10,
) -> str:
    """Search the library catalogue by title, author, genre, or keyword.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        query: Search text (title, author, keyword).
        genre: Filter by genre (e.g., "Fiction", "Science Fiction").
        author: Filter by author name.
        item_type: Filter by type: book, audiobook, dvd, ebook, magazine.
        limit: Max results (default 10, max 50).

    Returns:
        JSON string with matching books.
    """
    params: dict = {"q": query, "limit": min(limit, 50)}
    if genre:
        params["genre"] = genre
    if author:
        params["author"] = author
    if item_type:
        params["item_type"] = item_type

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/books",
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

"""Admin book management tools for the PageTurn MCP server."""

from typing import Any

import httpx


async def create_book(
    api_base_url: str,
    api_key: str,
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
    """Add a new book to the catalogue (admin only).

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication (must be admin scope).
        title: Book title.
        author: Author name.
        isbn: ISBN-10 (optional).
        isbn13: ISBN-13 (optional).
        description: Book description (optional).
        genre: Primary genre (optional).
        genres: All genres (optional).
        item_type: book/audiobook/dvd/ebook/magazine (optional).
        cover_image_url: URL to cover image (optional).
        page_count: Number of pages (optional).
        publication_year: Year published (optional).
        publisher: Publisher name (optional).
        copies: Number of copies to create, default 1 (optional).

    Returns:
        JSON string confirming creation with book_id.
    """
    body: dict[str, Any] = {"title": title, "author": author}
    if isbn is not None:
        body["isbn"] = isbn
    if isbn13 is not None:
        body["isbn13"] = isbn13
    if description is not None:
        body["description"] = description
    if genre is not None:
        body["genre"] = genre
    if genres is not None:
        body["genres"] = genres
    if item_type is not None:
        body["item_type"] = item_type
    if cover_image_url is not None:
        body["cover_image_url"] = cover_image_url
    if page_count is not None:
        body["page_count"] = page_count
    if publication_year is not None:
        body["publication_year"] = publication_year
    if publisher is not None:
        body["publisher"] = publisher
    if copies is not None:
        body["copies"] = copies

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{api_base_url}/api/admin/books",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def update_book(
    api_base_url: str,
    api_key: str,
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
    """Edit an existing book's metadata (admin only).

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication (must be admin scope).
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

    Returns:
        JSON string confirming the update.
    """
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if author is not None:
        body["author"] = author
    if isbn is not None:
        body["isbn"] = isbn
    if isbn13 is not None:
        body["isbn13"] = isbn13
    if description is not None:
        body["description"] = description
    if genre is not None:
        body["genre"] = genre
    if genres is not None:
        body["genres"] = genres
    if item_type is not None:
        body["item_type"] = item_type
    if cover_image_url is not None:
        body["cover_image_url"] = cover_image_url
    if page_count is not None:
        body["page_count"] = page_count
    if publication_year is not None:
        body["publication_year"] = publication_year
    if publisher is not None:
        body["publisher"] = publisher

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.put(
            f"{api_base_url}/api/admin/books/{book_id}",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def delete_book(
    api_base_url: str,
    api_key: str,
    book_id: str,
) -> str:
    """Remove a book from the catalogue (admin only).

    Fails if any copies are currently on loan.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication (must be admin scope).
        book_id: UUID of the book to delete.

    Returns:
        JSON string confirming deletion.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.delete(
            f"{api_base_url}/api/admin/books/{book_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def add_copies(
    api_base_url: str,
    api_key: str,
    book_id: str,
    count: int,
    condition: str | None = None,
) -> str:
    """Add copies to an existing book to increase inventory (admin only).

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication (must be admin scope).
        book_id: UUID of the book.
        count: Number of copies to add.
        condition: Condition of new copies: new, good, fair, poor (default "new").

    Returns:
        JSON string with number of copies created and new total copy count.
    """
    body: dict[str, Any] = {"count": count}
    if condition is not None:
        body["condition"] = condition

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{api_base_url}/api/admin/books/{book_id}/copies",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

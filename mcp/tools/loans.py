"""Loan management tools for the PageTurn MCP server."""

import httpx


async def get_my_loans(
    api_base_url: str,
    api_key: str,
) -> str:
    """List the user's current active loans.

    Returns:
        JSON string with active loans including book info, due dates,
        days remaining, and renewal eligibility.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/loans",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def get_loan_history(
    api_base_url: str,
    api_key: str,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """List the user's past loans.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        limit: Max results (default 20).
        offset: Skip N results for pagination.

    Returns:
        JSON string with returned loans including dates and review status.
    """
    params: dict = {"limit": limit, "offset": offset}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/loans/history",
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def checkout_book(
    api_base_url: str,
    api_key: str,
    book_id: str,
) -> str:
    """Check out a book or join the waitlist if unavailable.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        book_id: UUID of the book to check out.

    Returns:
        JSON string with loan details and due date on success,
        or waitlist position if the book is unavailable.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{api_base_url}/api/loans",
            json={"book_id": book_id},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def renew_loan(
    api_base_url: str,
    api_key: str,
    loan_id: str,
) -> str:
    """Renew an active loan to extend the due date.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        loan_id: UUID of the loan to renew.

    Returns:
        JSON string with new due date on success, or error explaining
        why renewal is blocked.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{api_base_url}/api/loans/{loan_id}/renew",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

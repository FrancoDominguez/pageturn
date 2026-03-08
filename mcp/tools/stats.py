"""Admin reporting and statistics tools for the PageTurn MCP server."""

import httpx


async def get_overdue_report(
    api_base_url: str,
    api_key: str,
) -> str:
    """Get a list of all overdue loans with user and fine info (admin only).

    Returns:
        JSON string with overdue loans including user name, book title,
        due date, days overdue, and fine amount.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/admin/loans",
            params={"status": "overdue"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def get_stats(
    api_base_url: str,
    api_key: str,
) -> str:
    """Get library-wide statistics (admin only).

    Returns:
        JSON string with total books, total copies, active loans,
        overdue loans, total users, and open fines amount.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/admin/stats",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

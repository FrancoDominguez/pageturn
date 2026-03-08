"""User management tools for the PageTurn MCP server (admin only)."""

import httpx


async def lookup_user(
    api_base_url: str,
    api_key: str,
    query: str,
) -> str:
    """Search for a user by name or email (admin only).

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication (must be admin scope).
        query: Name or email to search.

    Returns:
        JSON string with matching users including id, name, email, role,
        active loans count, and total fines.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/admin/users",
            params={"q": query},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def get_user_details(
    api_base_url: str,
    api_key: str,
    user_id: str,
) -> str:
    """Get full profile of a user including loans, fines, and reviews (admin only).

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication (must be admin scope).
        user_id: UUID of the user.

    Returns:
        JSON string with the user's full profile, current loans, loan history,
        active reservations, fines, and reviews.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

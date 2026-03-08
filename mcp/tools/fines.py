"""Fine management tools for the PageTurn MCP server."""

import httpx


async def get_my_fines(
    api_base_url: str,
    api_key: str,
) -> str:
    """View the user's outstanding fines and dues.

    Returns:
        JSON string with fines including amounts, reasons, statuses,
        and total outstanding balance.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/fines",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def waive_fine(
    api_base_url: str,
    api_key: str,
    fine_id: str,
) -> str:
    """Waive a fine for a user (admin only).

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication (must be admin scope).
        fine_id: UUID of the fine to waive.

    Returns:
        JSON string confirming the fine was waived.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{api_base_url}/api/admin/fines/{fine_id}/waive",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

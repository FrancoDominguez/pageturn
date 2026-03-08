"""Reservation tools for the PageTurn MCP server."""

import httpx


async def get_my_reservations(
    api_base_url: str,
    api_key: str,
) -> str:
    """List the user's active reservations.

    Returns:
        JSON string with reservations including status, queue position,
        and expiry time.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/reservations",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text


async def cancel_reservation(
    api_base_url: str,
    api_key: str,
    reservation_id: str,
) -> str:
    """Cancel a pending or ready reservation.

    Args:
        api_base_url: Base URL of the PageTurn REST API.
        api_key: Bearer token for authentication.
        reservation_id: UUID of the reservation to cancel.

    Returns:
        JSON string confirming cancellation.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.delete(
            f"{api_base_url}/api/reservations/{reservation_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

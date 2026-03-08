"""Reading profile tools for the PageTurn MCP server."""

import httpx


async def get_reading_profile(
    api_base_url: str,
    api_key: str,
) -> str:
    """Get the user's aggregated reading profile for personalized recommendations.

    Returns:
        JSON string with total books read, top 3 favorite genres and authors
        by count, average rating given, last 5 reads, and books rated 4-5 stars.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{api_base_url}/api/me/reading-profile",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.text

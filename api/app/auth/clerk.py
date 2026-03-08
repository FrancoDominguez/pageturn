import time

import httpx
from jose import jwt, jwk

from app.config import settings

_jwks_cache: dict = {}
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_cache_time
    if _jwks_cache and (time.time() - _jwks_cache_time) < JWKS_CACHE_TTL:
        return _jwks_cache

    async with httpx.AsyncClient() as client:
        # Clerk JWKS endpoint
        resp = await client.get(
            "https://api.clerk.com/v1/jwks",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
        )
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = time.time()
        return _jwks_cache


async def verify_clerk_jwt(token: str) -> dict:
    """Verify a Clerk JWT and return the claims."""
    jwks_data = await _get_jwks()

    # Get the signing key
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    rsa_key = None
    for key in jwks_data.get("keys", []):
        if key.get("kid") == kid:
            rsa_key = jwk.construct(key)
            break

    if not rsa_key:
        raise ValueError("Unable to find matching signing key")

    # Decode and verify
    claims = jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )

    return claims

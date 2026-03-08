"""PageTurn MCP Server — Main entry point.

Mounts user and admin MCP servers on /user and /admin paths,
with API key authentication middleware.

Run with:
    uvicorn server:app --host 0.0.0.0 --port 8080
"""

import json
import logging

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from auth import verify_api_key
from user_server import mcp as user_mcp
from admin_server import mcp as admin_mcp

logger = logging.getLogger("pageturn.mcp")


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate MCP requests using API keys.

    Extracts the Bearer token from the Authorization header, verifies it
    against the database, and stores the user context and raw key in
    request.state for tools to access.

    The /user path accepts both user and admin scoped keys.
    The /admin path requires admin scoped keys.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Health check bypasses auth
        if request.url.path == "/health":
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Missing or invalid Authorization header"},
                status_code=401,
            )

        api_key = auth_header[7:]

        # Determine required scope from the path
        required_scope = None
        if request.url.path.startswith("/admin"):
            required_scope = "admin"

        # Verify the API key
        try:
            user_context = await verify_api_key(api_key, required_scope)
        except ValueError as exc:
            return JSONResponse(
                {"error": str(exc)},
                status_code=401,
            )

        # Store user context and raw key in request state for tools
        request.state.user_context = user_context
        request.state.api_key = api_key

        logger.info(
            "Authenticated request: user_id=%s scope=%s path=%s",
            user_context["user_id"],
            user_context["scope"],
            request.url.path,
        )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Cloud Run."""
    return JSONResponse({"status": "ok", "service": "pageturn-mcp"})


# ---------------------------------------------------------------------------
# Starlette app
# ---------------------------------------------------------------------------

app = Starlette(
    routes=[
        Route("/health", health_check),
        Mount("/user", app=user_mcp.streamable_http_app()),
        Mount("/admin", app=admin_mcp.streamable_http_app()),
    ],
    middleware=[
        Middleware(APIKeyAuthMiddleware),
    ],
)

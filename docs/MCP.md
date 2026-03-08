# PageTurn — MCP Server Specification

**Protocol**: Model Context Protocol (MCP)
**Transport**: Streamable HTTP (modern standard)
**Hosting**: Google Cloud Run (single container, two route paths)
**SDK**: `mcp` Python SDK (latest)
**Auth**: API key in `Authorization: Bearer` header

---

## Architecture

```
Claude Desktop / AI Agent
    │
    ├── User MCP: POST https://mcp.pageturn.app/user
    │     └── Tools: search, loans, reservations, reviews, fines
    │
    └── Admin MCP: POST https://mcp.pageturn.app/admin
          └── Tools: all user tools + book CRUD, user mgmt, fine waive
```

Both MCP servers run in the same Cloud Run container. The route determines which tool set is exposed. Auth determines which user's data is accessed.

---

## Authentication Flow

1. User generates an API key in the PageTurn web app (AI Assistant page)
2. Key format: `pt_usr_<32hex>` (user scope) or `pt_adm_<32hex>` (admin scope)
3. User configures Claude Desktop with the MCP server URL and API key
4. On each MCP request:
   - Extract `Authorization: Bearer <key>` header
   - Hash the key with SHA-256
   - Look up `api_keys` table by `key_hash`
   - Verify: not revoked, not expired, scope matches endpoint (`/user` accepts both, `/admin` requires admin scope)
   - Resolve `user_id` from the API key record
   - All tool operations execute as that user

**Claude Desktop Configuration** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "pageturn": {
      "url": "https://mcp.pageturn.app/user",
      "headers": {
        "Authorization": "Bearer pt_usr_a1b2c3d4e5f6..."
      }
    }
  }
}
```

For admin:
```json
{
  "mcpServers": {
    "pageturn-admin": {
      "url": "https://mcp.pageturn.app/admin",
      "headers": {
        "Authorization": "Bearer pt_adm_a1b2c3d4e5f6..."
      }
    }
  }
}
```

---

## Server Implementation Pattern

```python
# mcp/user_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PageTurn Library")

@mcp.tool()
async def search_books(query: str, genre: str = None, author: str = None,
                       item_type: str = None, limit: int = 10) -> dict:
    """Search the library catalogue by title, author, genre, or keyword.

    Args:
        query: Search text (title, author, keyword)
        genre: Filter by genre (e.g., "Fiction", "Science Fiction")
        author: Filter by author name
        item_type: Filter by type: book, audiobook, dvd, ebook, magazine
        limit: Max results (default 10, max 50)
    """
    # Call the PageTurn API internally
    response = await api_client.get("/api/books", params={
        "q": query, "genre": genre, "author": author,
        "item_type": item_type, "limit": min(limit, 50)
    })
    return response.json()
```

The MCP server acts as a **thin wrapper** around the REST API. It:
1. Receives tool calls from the AI agent
2. Translates them into API calls (with the user's auth context)
3. Returns structured data the AI can reason about

This means all business logic lives in the API, not in the MCP server.

---

## User MCP Tools

### `search_books`
Search the library catalogue.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | yes | Search text |
| genre | string | no | Genre filter |
| author | string | no | Author filter |
| item_type | string | no | book/audiobook/dvd/ebook/magazine |
| limit | int | no | Max results (default 10) |

**Returns**: List of matching books with title, author, genre, rating, availability, cover URL.

**API Call**: `GET /api/books?q={query}&genre={genre}&...`

---

### `get_book_details`
Get full information about a specific book.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| book_id | string | yes | UUID of the book |

**Returns**: Complete book metadata, availability status, copy count, earliest return date, user's loan/reservation status.

**API Call**: `GET /api/books/{book_id}`

---

### `get_my_loans`
List the user's current active loans.

**Parameters**: None

**Returns**: List of active loans with book info, due dates, days remaining, renewal eligibility.

**API Call**: `GET /api/loans`

---

### `get_loan_history`
List the user's past loans.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| limit | int | no | Max results (default 20) |
| offset | int | no | Skip N results |

**Returns**: List of returned loans with dates and review status.

**API Call**: `GET /api/loans/history?limit={limit}&offset={offset}`

---

### `checkout_book`
Check out a book or join the waitlist if unavailable.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| book_id | string | yes | UUID of the book |

**Returns**: Success with loan details and due date, or waitlist position if unavailable.

**API Call**: `POST /api/loans` body: `{"book_id": book_id}`

---

### `renew_loan`
Renew an active loan to extend the due date.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| loan_id | string | yes | UUID of the loan |

**Returns**: Success with new due date, or error explaining why renewal is blocked.

**API Call**: `POST /api/loans/{loan_id}/renew`

---

### `get_my_reservations`
List the user's active reservations.

**Parameters**: None

**Returns**: List of reservations with status, queue position, expiry time.

**API Call**: `GET /api/reservations`

---

### `cancel_reservation`
Cancel a pending or ready reservation.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| reservation_id | string | yes | UUID of the reservation |

**Returns**: Confirmation of cancellation.

**API Call**: `DELETE /api/reservations/{reservation_id}`

---

### `get_my_fines`
View outstanding fines and dues.

**Parameters**: None

**Returns**: List of fines with amounts, reasons, statuses, and total outstanding balance.

**API Call**: `GET /api/fines`

---

### `get_my_reviews`
Get all reviews the user has written.

**Parameters**: None

**Returns**: List of reviews with book info, ratings, and review text. Useful for the AI to understand reading preferences.

**API Call**: `GET /api/reviews/mine`

---

### `get_book_reviews`
Get public reviews for a specific book.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| book_id | string | yes | UUID of the book |

**Returns**: Reviews from all users, average rating, rating distribution.

**API Call**: `GET /api/books/{book_id}/reviews`

---

### `create_review`
Rate and optionally review a book the user has borrowed.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| book_id | string | yes | UUID of the book |
| rating | int | yes | 1-5 star rating |
| review_text | string | no | Optional written review |

**Returns**: Created/updated review confirmation.

**API Call**: `POST /api/reviews` body: `{"book_id": ..., "rating": ..., "review_text": ...}`

---

### `get_reading_profile`
Get the user's aggregated reading profile for personalized recommendations.

**Parameters**: None

**Returns**: Total books read, top 3 favorite genres and authors by count, average rating given, last 5 reads, and books rated 4-5★.

**API Call**: `GET /api/me/reading-profile`

---

## Admin MCP Tools (Additional)

All 12 user tools above are available, plus:

### `create_book`
Add a new book to the catalogue.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| title | string | yes | Book title |
| author | string | yes | Author name |
| isbn | string | no | ISBN-10 |
| isbn13 | string | no | ISBN-13 |
| description | string | no | Book description |
| genre | string | no | Primary genre |
| genres | list[str] | no | All genres |
| item_type | string | no | book/audiobook/dvd/ebook/magazine |
| cover_image_url | string | no | URL to cover image |
| page_count | int | no | Number of pages |
| publication_year | int | no | Year published |
| publisher | string | no | Publisher name |
| copies | int | no | Number of copies to create (default 1) |

**API Call**: `POST /api/admin/books`

---

### `update_book`
Edit an existing book's metadata.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| book_id | string | yes | UUID of the book |
| title | string | no | Updated title |
| author | string | no | Updated author |
| description | string | no | Updated description |
| genre | string | no | Updated genre |
| (any book field) | various | no | Any updatable field |

**API Call**: `PUT /api/admin/books/{book_id}`

---

### `delete_book`
Remove a book from the catalogue (fails if copies are on loan).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| book_id | string | yes | UUID of the book |

**API Call**: `DELETE /api/admin/books/{book_id}`

---

### `lookup_user`
Search for a user by name or email.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | yes | Name or email to search |

**API Call**: `GET /api/admin/users?q={query}`

---

### `get_user_details`
Get full profile of a user including loans, fines, and reviews.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| user_id | string | yes | UUID of the user |

**API Call**: `GET /api/admin/users/{user_id}`

---

### `process_return`
Mark a book as returned. Calculates fines if overdue.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| loan_id | string | yes | UUID of the loan |

**API Call**: `POST /api/admin/loans/{loan_id}/return`

---

### `waive_fine`
Waive a fine for a user.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| fine_id | string | yes | UUID of the fine |

**API Call**: `POST /api/admin/fines/{fine_id}/waive`

---

### `get_overdue_report`
Get a list of all overdue loans with user and fine info.

**Parameters**: None

**API Call**: `GET /api/admin/loans?status=overdue`

---

### `get_stats`
Get library-wide statistics.

**Parameters**: None

**API Call**: `GET /api/admin/stats`

---

## Recommendation Strategy

The MCP intentionally does NOT include a recommendation tool. Instead, the AI agent builds recommendations by combining data from multiple tools:

0. **`get_reading_profile`** → Aggregated summary (reduces 3-4 tool calls to 1)
1. **`get_loan_history`** → What the user has read
2. **`get_my_reviews`** → What they liked/disliked and why
3. **`search_books`** → What's available in the catalogue
4. **`get_book_reviews`** → What other readers think

The agent uses its own intelligence to:
- Identify patterns in the user's reading (favorite genres, authors, themes)
- Cross-reference with available books
- Consider ratings from other readers
- Suggest books with personalized reasoning

This approach is better than a built-in algorithm because:
- The LLM understands nuance in review text (not just star ratings)
- It can explain WHY it's recommending something
- It adapts to conversational context ("I want something lighter this time")
- Zero engineering effort on our side — the intelligence is in the AI

---

## Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run with uvicorn, the MCP SDK handles HTTP transport
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### `requirements.txt`

```
mcp>=1.0.0
httpx>=0.27.0
uvicorn>=0.27.0
```

### Cloud Run Deployment

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/pageturn-mcp

# Deploy
gcloud run deploy pageturn-mcp \
  --image gcr.io/PROJECT_ID/pageturn-mcp \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql://...,API_BASE_URL=https://api.pageturn.app" \
  --memory 256Mi \
  --min-instances 0 \
  --max-instances 10
```

### Server Entry Point (`server.py`)

```python
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP
from auth import verify_api_key, get_user_from_key

# User MCP
user_mcp = FastMCP("PageTurn Library")
# ... register user tools ...

# Admin MCP
admin_mcp = FastMCP("PageTurn Admin")
# ... register all user tools + admin tools ...

# Starlette app with route-based MCP mounting
app = Starlette(routes=[
    Mount("/user", app=user_mcp.streamable_http_app()),
    Mount("/admin", app=admin_mcp.streamable_http_app()),
])

# Auth middleware applied to both routes
# Extracts API key, verifies scope, injects user context
```

The exact MCP SDK mounting pattern should be verified against the latest `mcp` package docs at implementation time, as the SDK is actively evolving.

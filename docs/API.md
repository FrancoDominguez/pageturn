# PageTurn — API Specification

**Framework**: FastAPI 0.109+
**Auth**: Clerk JWT verification
**Validation**: Pydantic v2
**Base URL**: `https://api.pageturn.app` (Vercel deployment)

---

## Authentication

### Clerk JWT
All authenticated endpoints require `Authorization: Bearer <clerk_jwt>` header.

**Middleware** (`app/auth/clerk.py`):
1. Extract JWT from `Authorization` header
2. Verify signature using Clerk's JWKS endpoint (cache keys for 1 hour)
3. Extract `sub` (Clerk user ID) from token payload
4. Look up user in DB by `clerk_id`
5. Attach `current_user` to request state

**Dependencies**:
- `get_current_user`: Returns user or raises 401
- `get_current_user_optional`: Returns user or None (for public endpoints that behave differently for logged-in users)
- `require_admin`: Calls `get_current_user`, then checks `role='admin'` or raises 403

### API Key Auth (MCP only)
MCP endpoints use `Authorization: Bearer pt_usr_xxx` or `pt_adm_xxx`.

1. Extract key from header
2. Compute SHA-256 hash
3. Look up in `api_keys` table by hash
4. Verify not revoked and not expired
5. Resolve user from `api_key.user_id`
6. Update `last_used_at`

---

## Public Endpoints (No Auth)

### `GET /api/books`

Search and browse the book catalogue.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| q | string | — | Free-text search query |
| genre | string | — | Filter by genre (exact match) |
| author | string | — | Filter by author (partial match) |
| item_type | string | — | Filter: book, audiobook, dvd, ebook, magazine |
| available | boolean | — | If true, only show books with available copies |
| staff_picks | boolean | false | Filter to staff picks only |
| sort | string | relevance | relevance, title_asc, title_desc, rating_desc, year_desc |
| page | int | 1 | Page number |
| limit | int | 20 | Results per page (max 100) |

**Response** `200 OK`:
```json
{
  "books": [
    {
      "id": "uuid",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "genre": "Fiction",
      "item_type": "book",
      "cover_image_url": "https://...",
      "avg_rating": 4.2,
      "rating_count": 847,
      "publication_year": 1925,
      "is_staff_pick": false,
      "staff_pick_note": null,
      "available_copies": 2,
      "total_copies": 3
    }
  ],
  "total": 156,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

**SQL (with FTS)**:
```sql
SELECT b.*,
       COUNT(bc.id) FILTER (WHERE bc.status = 'available') as available_copies,
       COUNT(bc.id) as total_copies,
       ts_rank(b.search_vector, plainto_tsquery('english', :query)) as rank
FROM books b
LEFT JOIN book_copies bc ON bc.book_id = b.id
WHERE b.search_vector @@ plainto_tsquery('english', :query)
  AND (:genre IS NULL OR b.genre = :genre)
  AND (:item_type IS NULL OR b.item_type = :item_type)
GROUP BY b.id
ORDER BY rank DESC
LIMIT :limit OFFSET :offset;
```

---

### `GET /api/books/{book_id}`

Book detail with availability info.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "isbn": "0743273567",
  "isbn13": "9780743273565",
  "description": "Set in the Jazz Age...",
  "genre": "Fiction",
  "genres": ["Fiction", "Classics", "American Literature"],
  "item_type": "book",
  "cover_image_url": "https://...",
  "page_count": 180,
  "publication_year": 1925,
  "publisher": "Scribner",
  "language": "en",
  "avg_rating": 4.2,
  "rating_count": 847,
  "copies": [
    {"id": "uuid", "status": "available", "condition": "good"},
    {"id": "uuid", "status": "checked_out", "condition": "new"},
    {"id": "uuid", "status": "available", "condition": "fair"}
  ],
  "available_copies": 2,
  "total_copies": 3,
  "earliest_return_date": "2026-04-15T00:00:00Z",
  "reservation_count": 0,
  "user_loan": null,
  "user_reservation": null
}
```

If the requesting user is authenticated (optional), include:
- `user_loan`: their active loan for this book (if any)
- `user_reservation`: their active reservation (if any)

**Error** `404`:
```json
{"detail": "Book not found"}
```

---

### `GET /api/books/{book_id}/reviews`

Public reviews for a book.

**Query Parameters**:
| Param | Type | Default |
|-------|------|---------|
| page | int | 1 |
| limit | int | 20 |
| sort | string | recent | recent, rating_desc, rating_asc |

**Response** `200 OK`:
```json
{
  "reviews": [
    {
      "id": "uuid",
      "user_name": "John D.",
      "user_initial": "JD",
      "rating": 5,
      "review_text": "An absolute masterpiece...",
      "created_at": "2026-02-12T14:30:00Z"
    }
  ],
  "avg_rating": 4.2,
  "rating_count": 847,
  "rating_distribution": {"5": 320, "4": 280, "3": 150, "2": 65, "1": 32},
  "total": 847,
  "page": 1,
  "limit": 20
}
```

---

## User Endpoints (Clerk JWT Required)

### `GET /api/me`

Current user profile.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "max_loans": 5,
  "active_loan_count": 3,
  "outstanding_fines": 2.50,
  "created_at": "2025-06-15T10:00:00Z"
}
```

---

### `GET /api/me/reading-profile`

Aggregated reading profile for AI recommendations.

**Response** `200 OK`:
```json
{
  "total_books_read": 42,
  "favorite_genres": [{"name": "Science Fiction", "count": 12}, {"name": "Mystery", "count": 8}, {"name": "Fiction", "count": 7}],
  "favorite_authors": [{"name": "Isaac Asimov", "count": 4}, {"name": "Agatha Christie", "count": 3}, {"name": "George Orwell", "count": 2}],
  "avg_rating_given": 3.8,
  "recent_reads": [
    {"book_id": "uuid", "book_title": "Dune", "author": "Frank Herbert", "rating": 4, "returned_at": "2026-03-01T10:00:00Z"}
  ],
  "highly_rated": [
    {"book_id": "uuid", "book_title": "1984", "author": "George Orwell", "rating": 5}
  ]
}
```

**SQL**: Aggregate from returned loans joined with reviews. Top 3 genres and authors by count, last 5 reads, books rated 4-5★.

---

### `POST /api/loans`

Check out a book.

**Request Body**:
```json
{"book_id": "uuid"}
```

**Business Logic**:
1. Check user total outstanding fines < $10.00 (blocked when >= $10.00)
2. Check active loans < max_loans
3. Check if user has an active reservation for this book (status='ready')
   - If yes: fulfill reservation, use the reserved copy
4. If no reservation: find an available copy
   - If found: create loan, set copy status='checked_out'
   - If not found: auto-create reservation (see POST /api/reservations logic)
5. Calculate due_date based on item_type

**Response** `201 Created` (checkout success):
```json
{
  "loan": {
    "id": "uuid",
    "book_title": "The Great Gatsby",
    "book_id": "uuid",
    "copy_id": "uuid",
    "checked_out_at": "2026-03-07T15:00:00Z",
    "due_date": "2026-03-21T15:00:00Z",
    "status": "active"
  }
}
```

**Response** `201 Created` (auto-reservation when no copies available):
```json
{
  "reservation": {
    "id": "uuid",
    "book_id": "uuid",
    "book_title": "The Great Gatsby",
    "status": "pending",
    "queue_position": 2,
    "expires_at": null
  }
}
```

**Note**: A single endpoint returns two different response shapes. The frontend checks for the presence of `loan` vs `reservation` key to determine the outcome.

**Errors**:
- `400`: `{"detail": "Outstanding fines of $X.XX exceed $10 limit. Please resolve before checking out."}`
- `400`: `{"detail": "Loan limit reached (5/5 active loans)."}`
- `404`: `{"detail": "Book not found"}`
- `409`: `{"detail": "You already have this book checked out."}`

---

### `GET /api/loans`

List current user's active loans.

**Response** `200 OK`:
```json
{
  "loans": [
    {
      "id": "uuid",
      "book": {
        "id": "uuid",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "cover_image_url": "https://..."
      },
      "checked_out_at": "2026-03-01T10:00:00Z",
      "due_date": "2026-03-15T10:00:00Z",
      "days_remaining": 8,
      "renewed_count": 0,
      "can_renew": true,
      "renewal_blocked_reason": null,
      "status": "active",
      "accrued_fine": null,
      "daily_rate": null,
      "days_overdue": null
    }
  ]
}
```

`days_remaining` is negative if overdue. When `status='overdue'`, the response includes calculated fine fields:
- `accrued_fine`: current calculated fine amount (e.g., `3.50`)
- `daily_rate`: applicable daily rate for the item type (e.g., `0.25`)
- `days_overdue`: number of days past due date (e.g., `14`)

These fields are `null` for non-overdue loans.

`can_renew` is false if:
- `renewed_count >= 2`: reason = "Maximum renewals reached"
- Reservation exists for book: reason = "Another member is waiting for this book"
- Overdue > 7 days: reason = "Loan is overdue by more than 7 days"

---

### `GET /api/loans/{loan_id}`

Single loan detail for the current user.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "book": {
    "id": "uuid",
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "cover_image_url": "https://..."
  },
  "checked_out_at": "2026-03-01T10:00:00Z",
  "due_date": "2026-03-15T10:00:00Z",
  "returned_at": null,
  "days_remaining": 8,
  "renewed_count": 0,
  "can_renew": true,
  "renewal_blocked_reason": null,
  "status": "active",
  "accrued_fine": null,
  "daily_rate": null,
  "days_overdue": null
}
```

**Errors**:
- `404`: `{"detail": "Loan not found"}`

---

### `GET /api/loans/history`

User's loan history (returned books).

**Query**: `page`, `limit` (default 20)

**Response** `200 OK`:
```json
{
  "loans": [
    {
      "id": "uuid",
      "book": {
        "id": "uuid",
        "title": "1984",
        "author": "George Orwell",
        "cover_image_url": "https://..."
      },
      "checked_out_at": "2026-01-10T10:00:00Z",
      "returned_at": "2026-01-20T14:00:00Z",
      "was_late": false,
      "user_review": {
        "id": "uuid",
        "rating": 4
      }
    }
  ],
  "total": 42,
  "page": 1
}
```

---

### `POST /api/loans/{loan_id}/renew`

Renew an active loan.

**Business Logic**:
1. Verify loan belongs to current user
2. Verify loan status is 'active'
3. Verify `renewed_count < 2`
4. Check no pending reservations for this book:
   ```sql
   SELECT COUNT(*) FROM reservations
   WHERE book_id = (SELECT book_id FROM book_copies WHERE id = loan.book_copy_id)
   AND status = 'pending';
   ```
5. Check loan not overdue > 7 days
6. Update: `due_date = now() + loan_period`, `renewed_count += 1`

**Response** `200 OK`:
```json
{
  "loan_id": "uuid",
  "new_due_date": "2026-04-04T15:00:00Z",
  "renewed_count": 1,
  "can_renew_again": true
}
```

**Errors**:
- `400`: `{"detail": "Cannot renew — another member is waiting for this book"}`
- `400`: `{"detail": "Maximum renewals reached (2/2)"}`
- `400`: `{"detail": "Cannot renew — loan is overdue by more than 7 days"}`
- `404`: `{"detail": "Loan not found"}`

---

### `POST /api/reservations`

Reserve a book.

**Request Body**:
```json
{"book_id": "uuid"}
```

**Logic**:
1. Check user doesn't already have an active reservation for this book
2. Check user doesn't already have this book checked out
3. Find available copy:
   - If found: set copy status='reserved', create reservation status='ready', expires_at=now()+48h
   - If not found: create reservation status='pending', queue_position=max_position+1 for this book

**Response** `201 Created`:
```json
{
  "reservation": {
    "id": "uuid",
    "book_id": "uuid",
    "book_title": "The Great Gatsby",
    "status": "ready",
    "queue_position": null,
    "expires_at": "2026-03-09T15:00:00Z"
  }
}
```
or for waitlist:
```json
{
  "reservation": {
    "id": "uuid",
    "book_id": "uuid",
    "book_title": "The Great Gatsby",
    "status": "pending",
    "queue_position": 2,
    "expires_at": null
  }
}
```

---

### `GET /api/reservations`

User's active reservations.

**Response** `200 OK`:
```json
{
  "reservations": [
    {
      "id": "uuid",
      "book": {
        "id": "uuid",
        "title": "Dune",
        "author": "Frank Herbert",
        "cover_image_url": "https://..."
      },
      "status": "pending",
      "queue_position": 1,
      "expires_at": null,
      "reserved_at": "2026-03-05T10:00:00Z"
    }
  ]
}
```

---

### `DELETE /api/reservations/{reservation_id}`

Cancel a reservation.

**Logic**: Set status='cancelled'. If the reservation was 'ready', set the copy status back to 'available' and trigger next-in-queue check. If the reservation was 'pending', decrement `queue_position` by 1 for all reservations of the same book with a higher `queue_position` (handled atomically in a single transaction).

**Response** `200 OK`:
```json
{"message": "Reservation cancelled"}
```

---

### `GET /api/fines`

User's fines.

**Response** `200 OK`:
```json
{
  "fines": [
    {
      "id": "uuid",
      "book_title": "The Hobbit",
      "loan_id": "uuid",
      "amount": 3.50,
      "reason": "late_return",
      "status": "pending",
      "created_at": "2026-02-28T00:00:00Z"
    }
  ],
  "total_outstanding": 3.50,
  "checkout_blocked": false
}
```

`checkout_blocked` is true when `total_outstanding >= 10.00`.

---

### `POST /api/reviews`

Create or update a review.

**Request Body**:
```json
{
  "book_id": "uuid",
  "rating": 4,
  "review_text": "Great book, loved the prose."
}
```

**Validation**:
- Rating: 1-5 integer required
- Review text: optional, max 2000 chars
- User must have a loan (active or returned) for this book

**Response** `201 Created` or `200 OK` (if updating):
```json
{
  "review": {
    "id": "uuid",
    "book_id": "uuid",
    "rating": 4,
    "review_text": "Great book, loved the prose.",
    "created_at": "2026-03-07T15:00:00Z"
  }
}
```

**Logic**: Uses `INSERT ... ON CONFLICT (user_id, book_id) DO UPDATE` for upsert behavior.

---

### `GET /api/reviews/mine`

User's own reviews.

**Response** `200 OK`:
```json
{
  "reviews": [
    {
      "id": "uuid",
      "book": {
        "id": "uuid",
        "title": "1984",
        "cover_image_url": "https://..."
      },
      "rating": 5,
      "review_text": "Chillingly prophetic.",
      "created_at": "2026-02-01T10:00:00Z"
    }
  ]
}
```

---

### `DELETE /api/reviews/{review_id}`

Delete own review.

**Response** `200 OK`:
```json
{"message": "Review deleted"}
```

---

### `POST /api/api-keys`

Generate a new API key.

**Request Body**:
```json
{"name": "Claude Desktop"}
```

**Logic**:
1. Generate 32 random hex bytes
2. Determine scope: 'admin' if user is admin, else 'user'
3. Compose key: `pt_usr_<hex>` or `pt_adm_<hex>`
4. Store SHA-256 hash and first 8 chars as prefix
5. Return plaintext key ONCE

**Response** `201 Created`:
```json
{
  "api_key": {
    "id": "uuid",
    "name": "Claude Desktop",
    "key": "pt_usr_a1b2c3d4e5f6...",
    "key_prefix": "pt_usr_a1",
    "scope": "user",
    "created_at": "2026-03-07T15:00:00Z"
  },
  "warning": "Save this key — you won't be able to see it again."
}
```

---

### `GET /api/api-keys`

List user's API keys (no plaintext keys shown).

**Response** `200 OK`:
```json
{
  "api_keys": [
    {
      "id": "uuid",
      "name": "Claude Desktop",
      "key_prefix": "pt_usr_a1",
      "scope": "user",
      "last_used_at": "2026-03-07T10:00:00Z",
      "created_at": "2026-03-01T10:00:00Z",
      "is_active": true
    }
  ]
}
```

---

### `DELETE /api/api-keys/{key_id}`

Revoke an API key.

**Response** `200 OK`:
```json
{"message": "API key revoked"}
```

---

## Admin Endpoints (Clerk JWT + role='admin')

### `GET /api/admin/stats`

Dashboard statistics.

**Response** `200 OK`:
```json
{
  "total_books": 1000,
  "total_copies": 2400,
  "active_loans": 75,
  "overdue_loans": 25,
  "total_users": 50,
  "total_fines_outstanding": 342.50,
  "loans_today": 5,
  "returns_today": 3
}
```

---

### `POST /api/admin/books`

Create a new book.

**Request Body**:
```json
{
  "title": "New Book Title",
  "author": "Author Name",
  "isbn": "0123456789",
  "isbn13": "9780123456789",
  "description": "A great book about...",
  "genre": "Fiction",
  "genres": ["Fiction", "Literary Fiction"],
  "item_type": "book",
  "cover_image_url": "https://...",
  "page_count": 300,
  "publication_year": 2026,
  "publisher": "Publisher Name",
  "language": "en",
  "is_staff_pick": false,
  "staff_pick_note": null,
  "copies": 2,
  "copy_condition": "new"
}
```

`copies` and `copy_condition` are convenience fields — they create N book_copies with the given condition.

**Response** `201 Created`:
```json
{
  "book": { "id": "uuid", "title": "New Book Title", ... },
  "copies_created": 2
}
```

---

### `PUT /api/admin/books/{book_id}`

Update book metadata. Partial update — only provided fields are changed.

**Request Body** (all optional):
```json
{
  "title": "Updated Title",
  "description": "Updated description...",
  "genre": "Science Fiction"
}
```

**Response** `200 OK`:
```json
{"book": { "id": "uuid", ... }}
```

---

### `DELETE /api/admin/books/{book_id}`

Delete a book and all its copies.

**Logic**: Only allow if no active loans exist for any copy. If active loans exist, return error.

**Response** `200 OK`:
```json
{"message": "Book deleted", "copies_removed": 3}
```

**Error** `400`:
```json
{"detail": "Cannot delete — 2 copies are currently on loan"}
```

---

### `POST /api/admin/books/{book_id}/copies`

Add copies of a book.

**Request Body**:
```json
{"count": 3, "condition": "new"}
```

**Response** `201 Created`:
```json
{"copies_created": 3, "total_copies": 6}
```

---

### `GET /api/admin/users`

List all users.

**Query**: `q` (search by name/email), `role`, `page`, `limit`

**Response** `200 OK`:
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "user",
      "active_loans": 3,
      "outstanding_fines": 2.50,
      "created_at": "2025-06-15T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1
}
```

---

### `GET /api/admin/users/{user_id}`

User detail with all related data.

**Response** `200 OK`:
```json
{
  "user": {
    "id": "uuid",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "max_loans": 5,
    "created_at": "2025-06-15T10:00:00Z"
  },
  "active_loans": [...],
  "loan_history": [...],
  "reservations": [...],
  "fines": [...],
  "reviews": [...]
}
```

---

### `PUT /api/admin/users/{user_id}`

Update user fields (max_loans, role).

**Request Body**:
```json
{"max_loans": 10}
```

**Response** `200 OK`:
```json
{"user": {...}}
```

---

### `POST /api/admin/users/{user_id}/promote`

Promote user to admin or demote to user.

**Request Body**:
```json
{"role": "admin"}
```

**Logic**:
1. Update user.role in DB
2. Sync to Clerk publicMetadata via Clerk Backend API:
   ```python
   clerk.users.update(clerk_id, public_metadata={"role": "admin"})
   ```

**Response** `200 OK`:
```json
{"user_id": "uuid", "new_role": "admin"}
```

---

### `GET /api/admin/loans`

All active loans across all users.

**Query**: `status` (active/overdue), `page`, `limit`

**Response** `200 OK`:
```json
{
  "loans": [
    {
      "id": "uuid",
      "user": {"id": "uuid", "name": "John Doe", "email": "john@example.com"},
      "book": {"id": "uuid", "title": "The Great Gatsby"},
      "checked_out_at": "...",
      "due_date": "...",
      "days_overdue": 3,
      "status": "overdue"
    }
  ],
  "total": 100
}
```

---

### `POST /api/admin/loans/{loan_id}/return`

Process a book return.

**Logic**:
1. Set loan: `returned_at=now()`, `status='returned'`
2. Calculate fine if overdue → create fine record
3. Set copy status='available'
4. Trigger reservation queue check (process next pending reservation)

**Response** `200 OK`:
```json
{
  "loan_id": "uuid",
  "returned_at": "2026-03-07T15:00:00Z",
  "was_late": true,
  "fine": {
    "id": "uuid",
    "amount": 3.50,
    "reason": "late_return"
  },
  "reservation_triggered": true,
  "next_reservation_user": "Jane Smith"
}
```

---

### `POST /api/admin/loans/{loan_id}/lost`

Mark a loan as lost.

**Logic**:
1. Set loan: `returned_at=now()`, `status='returned'`
2. Create fine record with `reason='lost_item'`, amount = book's `replacement_cost` or $30.00 default
3. Set copy `status='lost'`

**Response** `200 OK`:
```json
{
  "loan_id": "uuid",
  "fine": {
    "id": "uuid",
    "amount": 30.00,
    "reason": "lost_item"
  },
  "copy_status": "lost"
}
```

**Errors**:
- `404`: `{"detail": "Loan not found"}`
- `400`: `{"detail": "Loan is not active"}`

---

### `PUT /api/admin/book-copies/{copy_id}`

Update a specific book copy's status or condition.

**Request Body** (all optional):
```json
{
  "status": "damaged",
  "condition": "poor"
}
```

**Logic**: Validates that the new status is one of: `available`, `damaged`, `lost`. Cannot set to `checked_out` or `reserved` directly (those are managed by loan/reservation flows).

**Response** `200 OK`:
```json
{
  "copy": {
    "id": "uuid",
    "book_id": "uuid",
    "barcode": "PT-0001-01",
    "status": "damaged",
    "condition": "poor"
  }
}
```

---

### `GET /api/admin/fines`

All fines.

**Query**: `status` (pending/paid/waived), `page`, `limit`

**Response** `200 OK`:
```json
{
  "fines": [
    {
      "id": "uuid",
      "user": {"id": "uuid", "name": "John Doe"},
      "book_title": "The Hobbit",
      "amount": 3.50,
      "reason": "late_return",
      "status": "pending",
      "created_at": "..."
    }
  ],
  "total": 40,
  "total_outstanding_amount": 342.50
}
```

---

### `POST /api/admin/fines/{fine_id}/waive`

Waive a fine.

**Logic**: Set `status='waived'`, `waived_by=current_admin.id`, `waived_at=now()`

**Response** `200 OK`:
```json
{"fine_id": "uuid", "status": "waived", "waived_by": "admin@example.com"}
```

---

## Webhook Endpoint

### `POST /api/webhooks/clerk`

Receives Clerk webhook events.

**Headers**: `svix-id`, `svix-timestamp`, `svix-signature` (verified using `CLERK_WEBHOOK_SECRET`)

**Events Handled**:
- `user.created` → INSERT into users
- `user.updated` → UPDATE users
- `user.deleted` → DELETE or deactivate users

**Response**: `200 OK` `{"received": true}`

**Implementation**:
```python
from svix.webhooks import Webhook

wh = Webhook(CLERK_WEBHOOK_SECRET)
payload = wh.verify(body, headers)  # Raises on invalid signature
```

---

## Error Response Format

All errors follow:
```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

Common error codes:
| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT/API key |
| `FORBIDDEN` | 403 | Insufficient permissions (not admin) |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request body |
| `CHECKOUT_BLOCKED` | 400 | Fines exceed threshold |
| `LOAN_LIMIT` | 400 | Max concurrent loans reached |
| `RENEWAL_BLOCKED` | 400 | Cannot renew (reservation pending, max reached, etc.) |
| `DUPLICATE` | 409 | Already exists (e.g., already checked out) |

---

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pageturn.app",         # Production frontend
        "http://localhost:5173",         # Local Vite dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

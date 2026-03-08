# PageTurn -- Testing Plan

## 1. Testing Strategy Overview

### 1.1 Testing Pyramid

PageTurn follows the standard testing pyramid, weighted toward unit and integration tests where the business logic is most dense.

```
        /  E2E  \          ~30 tests   (Playwright)
       /----------\
      / Integration \      ~120 tests  (pytest + httpx, React Testing Library)
     /----------------\
    /    Unit Tests     \  ~200 tests  (pytest, vitest)
   /____________________\
```

### 1.2 What to Test at Each Level

| Level | Scope | Examples |
|-------|-------|---------|
| Unit | Single function, no I/O | Fine calculation, loan period lookup, queue reordering logic, status derivation |
| Integration | Service + DB or API endpoint + DB | Checkout endpoint with all 6 preconditions, reservation queue on return, Clerk webhook processing |
| E2E | Full browser flow across multiple pages | Search a book, sign in, check out, view on loans page, renew, verify fine accrual |

### 1.3 Coverage Goals

| Layer | Target | Rationale |
|-------|--------|-----------|
| Backend unit (services) | 95% line coverage | Business logic is the core value; fine and loan rules must be provably correct |
| Backend integration (API) | 90% line coverage | Every endpoint path (success + every documented error) exercised at least once |
| Frontend unit (hooks, utils) | 80% line coverage | UI logic like status derivation, date formatting, availability display |
| Frontend component | Key components only | BookCard, StarRating, AvailabilityBadge, ProtectedRoute, ReviewForm |
| E2E | Critical paths (10 flows) | Enough to catch regressions in cross-page interactions |
| MCP | 100% tool coverage | Every tool invoked at least once with valid and invalid auth |

---

## 2. Unit Tests

### 2.1 Backend Unit Tests

All backend unit tests live under `api/tests/unit/`. They use plain pytest with no database connection; service functions receive mock/fake DB sessions.

#### 2.1.1 `test_fine_service.py` -- Fine Calculation

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Book returned on time | due=Mar 10, returned=Mar 10, type=book | Fine = $0.00 |
| 2 | Book returned 1 day late | due=Mar 10, returned=Mar 11, type=book | Fine = $0.25 |
| 3 | Book returned 14 days late | due=Mar 1, returned=Mar 15, type=book | Fine = $3.50 |
| 4 | DVD returned 5 days late | due=Mar 1, returned=Mar 6, type=dvd | Fine = $5.00 |
| 5 | Audiobook returned 10 days late | type=audiobook | Fine = $5.00 |
| 6 | Magazine returned 3 days late | type=magazine | Fine = $0.30 |
| 7 | Fine hits $25 cap (book, 120 days late) | type=book, 120 days | Fine = $25.00 (not $30.00) |
| 8 | Fine hits $25 cap (DVD, 30 days late) | type=dvd, 30 days | Fine = $25.00 (not $30.00) |
| 9 | Ebook uses same rate as book | type=ebook, 4 days late | Fine = $1.00 |
| 10 | Unknown item type defaults to $0.25 | type=unknown, 4 days | Fine = $1.00 |
| 11 | Lost item fee uses replacement_cost | replacement_cost=45.00 | Fine = $45.00 |
| 12 | Lost item fee uses $30 default when no replacement_cost | replacement_cost=None | Fine = $30.00 |
| 13 | Checkout blocked at exactly $10.00 | outstanding_total=10.00 | blocked=True |
| 14 | Checkout NOT blocked at $9.99 | outstanding_total=9.99 | blocked=False |
| 15 | Checkout NOT blocked at $0.00 | outstanding_total=0.00 | blocked=False |

#### 2.1.2 `test_loan_service.py` -- Loan Logic

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 1 | Loan period -- book | item_type=book | 14 days |
| 2 | Loan period -- ebook | item_type=ebook | 14 days |
| 3 | Loan period -- dvd | item_type=dvd | 7 days |
| 4 | Loan period -- magazine | item_type=magazine | 7 days |
| 5 | Loan period -- audiobook | item_type=audiobook | 21 days |
| 6 | Renewal extends from current date | renewed today, original period 14d | new due_date = today + 14d |
| 7 | Renewal increments renewed_count | was 0 | becomes 1 |
| 8 | Renewal blocked at max (2) | renewed_count=2 | raises error "Maximum renewals reached" |
| 9 | Renewal blocked when reservation exists | pending reservation for same book | raises error "another member is waiting" |
| 10 | Renewal blocked when overdue > 7 days | due 10 days ago | raises error "overdue by more than 7 days" |
| 11 | Renewal allowed when overdue <= 7 days | due 5 days ago | succeeds |
| 12 | Renewal allowed when renewed_count=1 | renewed_count=1 | succeeds, can_renew_again=False after |
| 13 | Due date calculation from checkout timestamp | checked_out_at=2026-03-01 12:00, book | due_date=2026-03-15 12:00 |

#### 2.1.3 `test_reservation_service.py` -- Reservation Queue Logic

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 1 | Queue position assignment | 2 existing pending reservations | new reservation gets position 3 |
| 2 | Queue reorder on cancel (middle) | Cancel position 2 of 3 | Position 3 becomes 2 |
| 3 | Queue reorder on cancel (first) | Cancel position 1 of 3 | Positions 2,3 become 1,2 |
| 4 | Queue reorder on cancel (last) | Cancel position 3 of 3 | No reordering needed |
| 5 | Queue reorder on cancel (only one) | Cancel position 1 of 1 | Empty queue |
| 6 | Immediate reserve when copy available | 1 copy available | status=ready, expires_at=now+48h |
| 7 | Waitlist when no copies available | 0 available copies | status=pending, queue_position assigned |
| 8 | Return triggers next-in-queue | Pending reservation exists | Copy set to reserved, reservation set to ready |
| 9 | Return with no pending reservations | No pending reservations | Copy stays available |
| 10 | Expiry triggers next-in-queue | Ready reservation expired, next pending exists | Next pending becomes ready |

#### 2.1.4 `test_search_service.py` -- Search Logic

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 1 | FTS matches title | query="gatsby" | Returns "The Great Gatsby" |
| 2 | FTS matches author | query="fitzgerald" | Returns books by Fitzgerald |
| 3 | FTS matches description keyword | query="jazz age" | Returns books with "jazz age" in description |
| 4 | Title has highest weight | query="dune" with a book titled "Dune" and another with "dune" in description | "Dune" ranks first |
| 5 | Genre filter narrows results | genre="Fiction" | Only fiction books returned |
| 6 | Item type filter | item_type="dvd" | Only DVDs returned |
| 7 | Available-only filter | available=true | Only books with available_copies > 0 |
| 8 | Staff picks filter | staff_picks=true | Only is_staff_pick=true books |
| 9 | Sort by rating descending | sort=rating_desc | Highest rated first |
| 10 | Sort by title A-Z | sort=title_asc | Alphabetical |
| 11 | Pagination returns correct page | page=2, limit=20 | Items 21-40 |
| 12 | Empty result set | query="xyznonexistent" | Empty list, total=0 |

#### 2.1.5 `test_api_key_service.py` -- API Key Logic

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 1 | Key generation format (user) | user.role=user | Key starts with "pt_usr_" |
| 2 | Key generation format (admin) | user.role=admin | Key starts with "pt_adm_" |
| 3 | Key hash is SHA-256 of full key | Generate and hash | hashlib.sha256(key).hexdigest() matches stored hash |
| 4 | Key prefix is first 10 chars | Generate key | key_prefix == key[:10] |
| 5 | Revoked key fails validation | revoked_at is set | Raises 401 |
| 6 | Expired key fails validation | expires_at < now | Raises 401 |

### 2.2 Frontend Unit Tests

All frontend unit tests live under `frontend/src/__tests__/`. They use vitest + React Testing Library.

#### 2.2.1 `test_utils.ts` -- Utility Functions

| # | Test | Function | Expected |
|---|------|----------|----------|
| 1 | getLoanStatus active | days_remaining=10 | "active" |
| 2 | getLoanStatus due-soon | days_remaining=2 | "due-soon" |
| 3 | getLoanStatus overdue | days_remaining=-3 | "overdue" |
| 4 | getLoanStatus boundary (3 days) | days_remaining=3 | "due-soon" |
| 5 | getLoanStatus boundary (0 days) | days_remaining=0 | "due-soon" |
| 6 | formatCurrency | 3.5 | "$3.50" |
| 7 | formatCurrency zero | 0 | "$0.00" |
| 8 | truncateText within limit | "short", limit=100 | "short" |
| 9 | truncateText over limit | "a".repeat(50), limit=20 | 20 chars + "..." |

#### 2.2.2 Component Tests

| # | Component | Test | Expected |
|---|-----------|------|----------|
| 1 | StarRating (display) | rating=3.5 | 3 full stars, 1 half star, 1 empty star |
| 2 | StarRating (input) | Click 4th star | onChange called with 4 |
| 3 | AvailabilityBadge | available_copies=2 | Green badge "Available -- 2 copies" |
| 4 | AvailabilityBadge | available_copies=0 | Orange badge "All copies checked out" |
| 5 | ItemTypeBadge | item_type="book" | Not rendered (default type) |
| 6 | ItemTypeBadge | item_type="dvd" | Rendered with disc icon |
| 7 | BookCard | Full book data | Renders title, author, rating, genre, availability |
| 8 | BookCard | Missing cover_image_url | Renders placeholder gradient |
| 9 | Pagination | page=3, pages=10 | Shows Previous, 1...3, 4, 5...10, Next |
| 10 | Pagination | page=1 | Previous is disabled |
| 11 | EmptyState | message + CTA | Renders message and button |
| 12 | ProtectedRoute | Signed out | Shows sign-in prompt |
| 13 | Modal | isOpen=true | Renders overlay + content |
| 14 | Modal | Press Escape | onClose called |
| 15 | Toast | variant=success | Green toast with message, auto-dismiss after 3s |

#### 2.2.3 Hook Tests

| # | Hook | Test | Expected |
|---|------|------|----------|
| 1 | useBookSearch | Successful fetch | Returns books array, isLoading transitions to false |
| 2 | useBookSearch | Error response | error is set, data is undefined |
| 3 | useMyLoans | Returns loans | loans array populated |
| 4 | useRenewLoan | Successful mutation | Invalidates my-loans query key |
| 5 | useCheckout | Successful checkout | Invalidates my-loans and book query keys |
| 6 | useCheckout | Auto-reservation response | Returns reservation data (not loan) |

---

## 3. Integration Tests

### 3.1 API Endpoint Tests

All API integration tests live under `api/tests/integration/`. They use `httpx.AsyncClient` with the FastAPI `TestClient` against a real test database.

#### 3.1.1 Public Endpoints

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 1 | `GET /api/books` | No params | Returns paginated list, 200 |
| 2 | `GET /api/books?q=gatsby` | FTS search | Results include "The Great Gatsby", 200 |
| 3 | `GET /api/books?genre=Fiction` | Genre filter | All results have genre=Fiction |
| 4 | `GET /api/books?item_type=dvd` | Type filter | All results have item_type=dvd |
| 5 | `GET /api/books?available=true` | Availability filter | All results have available_copies > 0 |
| 6 | `GET /api/books?staff_picks=true` | Staff picks filter | All results have is_staff_pick=true |
| 7 | `GET /api/books?sort=rating_desc` | Sort by rating | First result has highest avg_rating |
| 8 | `GET /api/books?page=2&limit=5` | Pagination | Returns 5 results, page=2 |
| 9 | `GET /api/books?q=xyznothing` | No results | Empty books array, total=0, 200 |
| 10 | `GET /api/books/{valid_id}` | Book exists | Full detail with copies, 200 |
| 11 | `GET /api/books/{invalid_id}` | Book not found | 404 "Book not found" |
| 12 | `GET /api/books/{id}/reviews` | Reviews exist | Paginated reviews + avg_rating + distribution, 200 |
| 13 | `GET /api/books/{id}/reviews?sort=rating_desc` | Sort reviews | Highest rating first |

#### 3.1.2 User Endpoints -- Authentication

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 14 | `GET /api/me` without auth header | No token | 401 |
| 15 | `GET /api/me` with invalid JWT | Bad token | 401 |
| 16 | `GET /api/me` with valid JWT | Good token | 200, returns user profile |
| 17 | `GET /api/loans` without auth | No token | 401 |
| 18 | `POST /api/loans` without auth | No token | 401 |

#### 3.1.3 User Endpoints -- Loans

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 19 | `POST /api/loans` -- successful checkout | book_id with available copy | 201, loan object with due_date |
| 20 | `POST /api/loans` -- auto-reservation | book_id with no available copies | 201, reservation object with queue_position |
| 21 | `POST /api/loans` -- fines block | User has $10+ in fines | 400 "Outstanding fines...exceed $10 limit" |
| 22 | `POST /api/loans` -- loan limit | User at max_loans | 400 "Loan limit reached" |
| 23 | `POST /api/loans` -- already checked out | User already has this book | 409 "You already have this book checked out" |
| 24 | `POST /api/loans` -- book not found | Invalid book_id | 404 |
| 25 | `POST /api/loans` -- fulfills reservation | User has ready reservation | 201, loan created, reservation status=fulfilled |
| 26 | `POST /api/loans` -- due date by type (book) | item_type=book | due_date = checked_out_at + 14 days |
| 27 | `POST /api/loans` -- due date by type (dvd) | item_type=dvd | due_date = checked_out_at + 7 days |
| 28 | `POST /api/loans` -- due date by type (audiobook) | item_type=audiobook | due_date = checked_out_at + 21 days |
| 29 | `GET /api/loans` | User has active loans | Returns loans with days_remaining, can_renew |
| 30 | `GET /api/loans` | User has overdue loans | Returns loans with accrued_fine, daily_rate, days_overdue |
| 31 | `GET /api/loans/{id}` | Valid loan belonging to user | 200, single loan detail |
| 32 | `GET /api/loans/{id}` | Loan belongs to other user | 404 |
| 33 | `GET /api/loans/history` | User has returned loans | Paginated list with was_late, user_review |
| 34 | `POST /api/loans/{id}/renew` -- success | Eligible loan | 200, new_due_date, renewed_count incremented |
| 35 | `POST /api/loans/{id}/renew` -- max renewals | renewed_count=2 | 400 "Maximum renewals reached" |
| 36 | `POST /api/loans/{id}/renew` -- reservation exists | Pending reservation for book | 400 "another member is waiting" |
| 37 | `POST /api/loans/{id}/renew` -- overdue > 7 days | Overdue by 10 days | 400 "overdue by more than 7 days" |
| 38 | `POST /api/loans/{id}/renew` -- wrong user | Loan belongs to another user | 404 |

#### 3.1.4 User Endpoints -- Reservations

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 39 | `POST /api/reservations` -- immediate reserve | Available copy exists | 201, status=ready, expires_at set |
| 40 | `POST /api/reservations` -- waitlist | No available copies | 201, status=pending, queue_position assigned |
| 41 | `POST /api/reservations` -- duplicate | Already has active reservation | 409 or 400 |
| 42 | `POST /api/reservations` -- already checked out | User has active loan for book | 409 or 400 |
| 43 | `GET /api/reservations` | User has reservations | Returns list with status, queue_position, expires_at |
| 44 | `DELETE /api/reservations/{id}` -- cancel pending | Pending reservation | 200, queue positions decremented |
| 45 | `DELETE /api/reservations/{id}` -- cancel ready | Ready reservation | 200, copy set back to available |
| 46 | `DELETE /api/reservations/{id}` -- wrong user | Reservation belongs to other user | 404 |

#### 3.1.5 User Endpoints -- Fines

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 47 | `GET /api/fines` | User has fines | Returns fines, total_outstanding, checkout_blocked |
| 48 | `GET /api/fines` | No fines | Empty list, total_outstanding=0, checkout_blocked=false |
| 49 | `GET /api/fines` | Fines >= $10 | checkout_blocked=true |

#### 3.1.6 User Endpoints -- Reviews

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 50 | `POST /api/reviews` -- create | Valid book_id, rating=4 | 201, review created |
| 51 | `POST /api/reviews` -- upsert (update) | Same book_id again, rating=5 | 200, review updated |
| 52 | `POST /api/reviews` -- no loan | User never borrowed book | 400 or 403 |
| 53 | `POST /api/reviews` -- invalid rating | rating=0 | 422 validation error |
| 54 | `POST /api/reviews` -- invalid rating | rating=6 | 422 validation error |
| 55 | `POST /api/reviews` -- review_text too long | 2001 chars | 422 validation error |
| 56 | `GET /api/reviews/mine` | User has reviews | Returns list with book info |
| 57 | `DELETE /api/reviews/{id}` | Own review | 200, review deleted |
| 58 | `DELETE /api/reviews/{id}` | Other user's review | 404 |

#### 3.1.7 User Endpoints -- API Keys

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 59 | `POST /api/api-keys` | name="Test" | 201, returns plaintext key + warning |
| 60 | `POST /api/api-keys` | User role=user | Key starts with pt_usr_ |
| 61 | `POST /api/api-keys` | User role=admin | Key starts with pt_adm_ |
| 62 | `GET /api/api-keys` | Keys exist | Returns list with prefix (no plaintext) |
| 63 | `DELETE /api/api-keys/{id}` | Own key | 200, revoked_at set |
| 64 | `DELETE /api/api-keys/{id}` | Other user's key | 404 |

#### 3.1.8 User Endpoints -- Profile

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 65 | `GET /api/me` | Valid user | 200, profile with active_loan_count, outstanding_fines |
| 66 | `GET /api/me/reading-profile` | User with history | 200, favorite_genres, favorite_authors, avg_rating_given |
| 67 | `GET /api/me/reading-profile` | New user (no history) | 200, total_books_read=0, empty arrays |

#### 3.1.9 Admin Endpoints -- Authorization

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 68 | `GET /api/admin/stats` as user | role=user | 403 |
| 69 | `POST /api/admin/books` as user | role=user | 403 |
| 70 | `GET /api/admin/users` as user | role=user | 403 |
| 71 | `GET /api/admin/stats` as admin | role=admin | 200 |

#### 3.1.10 Admin Endpoints -- Book Management

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 72 | `POST /api/admin/books` | Full book data | 201, book + copies_created |
| 73 | `POST /api/admin/books` | Missing title | 422 |
| 74 | `POST /api/admin/books` | Missing author | 422 |
| 75 | `PUT /api/admin/books/{id}` | Update title | 200, title changed |
| 76 | `PUT /api/admin/books/{id}` | Partial update (description only) | 200, only description changed |
| 77 | `DELETE /api/admin/books/{id}` | No active loans | 200, book + copies deleted |
| 78 | `DELETE /api/admin/books/{id}` | Active loans exist | 400 "Cannot delete" |
| 79 | `POST /api/admin/books/{id}/copies` | count=3, condition=new | 201, 3 copies added |
| 80 | `PUT /api/admin/book-copies/{id}` | status=damaged | 200, copy updated |
| 81 | `PUT /api/admin/book-copies/{id}` | status=checked_out | 400 (not directly settable) |

#### 3.1.11 Admin Endpoints -- User Management

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 82 | `GET /api/admin/users` | No params | Paginated user list |
| 83 | `GET /api/admin/users?q=john` | Search by name | Filtered results |
| 84 | `GET /api/admin/users/{id}` | Valid user | Full detail with loans, fines, reviews |
| 85 | `PUT /api/admin/users/{id}` | max_loans=10 | 200, updated |
| 86 | `POST /api/admin/users/{id}/promote` | role=admin | 200, role changed (verify DB) |
| 87 | `POST /api/admin/users/{id}/promote` | role=user (demote) | 200, role changed |

#### 3.1.12 Admin Endpoints -- Loan Management

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 88 | `GET /api/admin/loans` | No filter | All active loans |
| 89 | `GET /api/admin/loans?status=overdue` | Overdue filter | Only overdue loans |
| 90 | `POST /api/admin/loans/{id}/return` -- on time | Not overdue | 200, no fine, copy available |
| 91 | `POST /api/admin/loans/{id}/return` -- late | 5 days overdue, book | 200, fine=$1.25, fine record created |
| 92 | `POST /api/admin/loans/{id}/return` -- triggers reservation | Pending reservation exists | 200, reservation_triggered=true, copy reserved |
| 93 | `POST /api/admin/loans/{id}/lost` | Active loan | 200, fine=$30, copy status=lost |
| 94 | `POST /api/admin/loans/{id}/lost` | Loan already returned | 400 "Loan is not active" |

#### 3.1.13 Admin Endpoints -- Fine Management

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 95 | `GET /api/admin/fines` | No filter | All fines + total_outstanding_amount |
| 96 | `GET /api/admin/fines?status=pending` | Status filter | Only pending fines |
| 97 | `POST /api/admin/fines/{id}/waive` | Pending fine | 200, status=waived, waived_by set |

#### 3.1.14 Admin Endpoints -- Dashboard

| # | Endpoint | Test | Expected |
|---|----------|------|----------|
| 98 | `GET /api/admin/stats` | Seeded data | Returns total_books, total_copies, active_loans, overdue_loans, total_users, total_fines_outstanding |

### 3.2 Database Integration Tests

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 99 | FTS trigger on insert | Insert a book | search_vector is populated |
| 100 | FTS trigger on update | Update book title | search_vector is updated |
| 101 | Rating trigger on review insert | Insert review (rating=5) on book with avg_rating=4.0 | Book avg_rating recalculated |
| 102 | Rating trigger on review update | Update review rating from 5 to 1 | Book avg_rating recalculated |
| 103 | Rating trigger on review delete | Delete only review | Book avg_rating=0, rating_count=0 |
| 104 | updated_at trigger | Update a user record | updated_at changes |
| 105 | calculate_fine SQL function | Call with known inputs | Returns correct amount |
| 106 | UNIQUE constraint on reviews | Insert duplicate (user_id, book_id) | Conflict / upsert behavior |
| 107 | CASCADE delete on book | Delete book with copies | Copies deleted |
| 108 | Reservation queue atomic reorder | Cancel middle reservation in transaction | All positions correct after commit |

### 3.3 Clerk Webhook Tests

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 109 | `user.created` event | Valid payload with svix signature | User inserted in DB, 200 |
| 110 | `user.updated` event | Updated first_name | User record updated |
| 111 | `user.deleted` event | Valid user | deleted_at set, related records preserved |
| 112 | Invalid signature | Bad svix-signature header | 401 or 400 |
| 113 | Missing headers | No svix headers | 400 |
| 114 | Unknown event type | event_type="org.created" | 200 (ignored gracefully) |

### 3.4 Cron Job Tests

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 115 | Overdue detection | 3 active loans past due_date | All 3 set to status=overdue |
| 116 | Overdue detection skips returned | Returned loan past due_date | Not marked overdue |
| 117 | Overdue detection idempotent | Already-overdue loan | No duplicate processing |
| 118 | Reservation expiry | Ready reservation with expires_at in the past | Set to expired, copy available |
| 119 | Reservation expiry triggers next-in-queue | Expired + pending reservation exists | Next pending becomes ready |
| 120 | Reservation expiry skip active | Ready reservation not yet expired | No change |
| 121 | Cron auth -- valid CRON_SECRET | Correct header | 200 |
| 122 | Cron auth -- missing CRON_SECRET | No header | 401 |

---

## 4. End-to-End Tests

All E2E tests use Playwright. They run against a seeded test database with known data.

### 4.1 Auth Bypass Strategy for Testing

Clerk does not support programmatic login in E2E tests easily. Strategy:

1. **Test user tokens**: Use Clerk's Backend API to generate test session tokens for known test users before each test suite run. Store them in environment variables.
2. **Cookie injection**: Use Playwright's `context.addCookies()` or `page.evaluate()` to set the Clerk session cookie directly, bypassing the sign-in modal.
3. **Dedicated test users**: Maintain 3 test users in Clerk (visitor, member, admin) with known credentials for any tests that must go through the actual sign-in flow.
4. **API-level auth mock**: For backend integration tests, bypass Clerk JWT verification with a test middleware that accepts a `X-Test-User-Id` header.

### 4.2 Critical User Flows

#### Flow 1: Book Discovery (Visitor)

```
1. Navigate to / (homepage)
2. Verify Featured Hero section renders with a staff pick
3. Verify genre accordion sections render with book cards
4. Click on a genre accordion to expand it
5. Verify horizontal scroll row appears with book cards
6. Type "science fiction" in the nav search bar, press Enter
7. Verify page transitions to search results grid
8. Verify results contain relevant books
9. Click genre chip "Fiction" to filter
10. Verify results update to only Fiction books
11. Click a book card
12. Verify book detail page loads with full metadata
13. Verify reviews section renders
14. Verify "More by [Author]" section renders (if applicable)
```
**Verifies**: F1 (search, filter, sort, pagination), F2 (detail page), F15 (staff picks), F16 (top rated)

#### Flow 2: Sign In and Checkout (Member)

```
1. Navigate to /books/{available_book_id}
2. Click "Check Out" button
3. Verify redirect to Clerk sign-in (or inject auth)
4. After auth, verify redirect back to book detail page
5. Click "Check Out" again
6. Verify green success banner: "Checked out! Due back [date]"
7. Verify toast notification appears
8. Click "View My Loans" link in the banner
9. Verify LoansPage shows the newly checked out book
10. Verify due date matches expected loan period for item type
```
**Verifies**: F3 (auth), F4 (checkout), F5 (loans view)

#### Flow 3: Auto-Reservation on Unavailable Book (Member)

```
1. Navigate to /books/{unavailable_book_id} (all copies checked out)
2. Verify orange badge "All copies checked out"
3. Click "Check Out" (which triggers auto-reservation)
4. Verify blue banner: "You're #N in the waitlist"
5. Navigate to /loans
6. Verify reservation appears in "My Reservations" section with queue position
7. Click "Cancel" on the reservation
8. Verify reservation removed from list
```
**Verifies**: F4 (auto-reservation), F6 (reservation display, cancel)

#### Flow 4: Renew a Loan (Member)

```
1. Navigate to /loans (user has an active, renewable loan)
2. Verify "Renew" link is active (not disabled)
3. Click "Renew"
4. Verify toast: "Renewed until [new date]"
5. Verify due date updated in the table
6. Verify renewed_count incremented
```
**Verifies**: F5 (renewal)

#### Flow 5: Renewal Blocked by Reservation (Member)

```
1. Set up: User A has a checked-out book, User B has a pending reservation for same book
2. Log in as User A
3. Navigate to /loans
4. Verify "Renew" button is disabled
5. Verify reason text: "Another member is waiting for this book"
```
**Verifies**: F5 (renewal blocking), F6 (reservation impact)

#### Flow 6: Review a Book (Member)

```
1. Navigate to /books/{id} (user has a returned loan, no review)
2. Scroll to Reviews section
3. Click "Write a Review"
4. Select 4 stars
5. Type review text
6. Click Submit
7. Verify review appears in the list
8. Verify average rating updates
9. Navigate to /reviews
10. Verify review appears in "My Reviews"
11. Click Edit, change rating to 5, save
12. Verify rating updated
13. Click Delete, confirm
14. Verify review removed
```
**Verifies**: F7 (create, edit, delete review, avg recalculation)

#### Flow 7: Fine Accrual and Checkout Block (Cross-Feature)

```
1. Set up: User has overdue loans totaling > $10 in fines
2. Log in as the user
3. Navigate to /loans
4. Verify overdue alert banner with accrued fine amount
5. Navigate to /fines
6. Verify stat cards show correct outstanding amount
7. Verify warning banner "checkout hold" is displayed
8. Navigate to /books/{available_book_id}
9. Verify coral banner: "Checkout paused -- $X.XX in outstanding fines"
10. Verify "Check Out" button is disabled
```
**Verifies**: F4 (checkout block), F5 (overdue display), F8 (fine display, checkout block)

#### Flow 8: Admin Book Management (Admin)

```
1. Log in as admin
2. Navigate to /admin/books
3. Click "Add Book"
4. Fill in title, author, genre, item_type, copies=2
5. Submit
6. Verify book appears in the admin table
7. Click the book's copy count to open CopyManagementModal
8. Verify 2 copies listed
9. Close modal, click "Edit" on the book
10. Change the description
11. Submit
12. Navigate to the public book detail page
13. Verify updated description is displayed
14. Navigate back to /admin/books
15. Click "Delete" on a book with no active loans
16. Confirm
17. Verify book removed from table
```
**Verifies**: F9 (admin book CRUD, copy management)

#### Flow 9: Admin User Management and Fine Waiver (Admin)

```
1. Log in as admin
2. Navigate to /admin/users
3. Search for a user by name
4. Click on the user row
5. Verify user detail page shows loans, fines, reviews
6. Click "Waive" on a pending fine
7. Verify fine status changes to "waived"
8. Navigate to /admin/fines
9. Verify the waived fine appears with correct status
```
**Verifies**: F10 (admin user management), F8 (admin fine waiver)

#### Flow 10: Admin Process Return Triggers Reservation (Admin)

```
1. Set up: Book has a pending reservation from User B. User A has the book checked out.
2. Log in as admin
3. Navigate to /admin/loans
4. Find User A's loan, click "Process Return"
5. Verify return processed
6. Verify reservation for User B is now "ready"
7. Log in as User B
8. Navigate to /loans
9. Verify ready reservation alert banner at top: "Your reservation for [Title] is ready!"
```
**Verifies**: F5 (return processing), F6 (return triggers reservation queue)

### 4.3 Responsive Design Tests

| # | Test | Viewport | Expected |
|---|------|----------|----------|
| 1 | Homepage | 375px (mobile) | Single column, stacked sections, hamburger menu |
| 2 | Book detail | 375px (mobile) | Single column, cover above metadata |
| 3 | Loans table | 768px (tablet) | Responsive table or card layout |
| 4 | Admin dashboard | 1024px (desktop) | Full sidebar + content area |

---

## 5. MCP Testing

All MCP tests live under `mcp/tests/`. They use pytest with httpx to call the MCP server endpoints.

### 5.1 Auth Validation Tests

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 1 | No auth header | Request to /user without Authorization | 401 |
| 2 | Invalid API key | pt_usr_invalidkey | 401 |
| 3 | Revoked API key | Previously valid, now revoked | 401 |
| 4 | User key on /user | pt_usr_... on /user endpoint | 200, accepted |
| 5 | Admin key on /user | pt_adm_... on /user endpoint | 200, accepted |
| 6 | User key on /admin | pt_usr_... on /admin endpoint | 403, rejected |
| 7 | Admin key on /admin | pt_adm_... on /admin endpoint | 200, accepted |

### 5.2 User Tool Tests

| # | Tool | Test | Expected |
|---|------|------|----------|
| 8 | search_books | query="fiction" | Returns book list |
| 9 | search_books | query="", genre="Mystery" | Filtered results |
| 10 | get_book_details | Valid book_id | Full book metadata |
| 11 | get_book_details | Invalid book_id | Error response |
| 12 | get_my_loans | User has loans | Returns loan list |
| 13 | get_my_loans | User has no loans | Empty list |
| 14 | get_loan_history | limit=5 | Returns at most 5 results |
| 15 | checkout_book | Available book | Success with loan details |
| 16 | checkout_book | Unavailable book | Success with reservation/waitlist |
| 17 | checkout_book | Fines block | Error with fine amount |
| 18 | renew_loan | Valid renewable loan | Success with new due_date |
| 19 | renew_loan | Max renewals reached | Error message |
| 20 | get_my_reservations | Has reservations | Returns list |
| 21 | cancel_reservation | Valid reservation | Success |
| 22 | get_my_fines | Has fines | Returns fines + total |
| 23 | get_my_reviews | Has reviews | Returns list |
| 24 | get_book_reviews | Valid book_id | Returns reviews + avg_rating |
| 25 | create_review | Valid book_id, rating=4 | Success |
| 26 | create_review | Book not borrowed | Error |
| 27 | get_reading_profile | User with history | Returns aggregated profile |

### 5.3 Admin Tool Tests

| # | Tool | Test | Expected |
|---|------|------|----------|
| 28 | create_book | title + author | Success with book_id |
| 29 | update_book | Change description | Success |
| 30 | delete_book | No active loans | Success |
| 31 | delete_book | Active loans exist | Error |
| 32 | lookup_user | query="john" | Returns matching users |
| 33 | get_user_details | Valid user_id | Full profile |
| 34 | process_return | Active loan | Success, fine if overdue |
| 35 | waive_fine | Pending fine | Success |
| 36 | get_overdue_report | Overdue loans exist | Returns list |
| 37 | get_stats | Seeded data | Returns all stat fields |

### 5.4 MCP Scope Enforcement

| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 38 | User calls admin tool via /admin | User key on admin endpoint | 403 |
| 39 | User tools available on /admin | Admin key, call search_books | Success (admin has all user tools) |
| 40 | Admin tools NOT on /user | Admin key on /user, call create_book | Tool not found |

---

## 6. Performance Tests

Performance tests run against a staging environment with the full seeded dataset (1000 books, 50 users, 500 loans). Use k6 or locust for load testing and Playwright for page load measurements.

### 6.1 API Response Time Tests

| # | Test | Endpoint | Target | Method |
|---|------|----------|--------|--------|
| 1 | Search response time | `GET /api/books?q=fiction` | < 200ms p95 | k6 with 50 concurrent users |
| 2 | Search with filters | `GET /api/books?q=sci&genre=Fiction&available=true` | < 200ms p95 | k6 |
| 3 | Book detail response | `GET /api/books/{id}` | < 500ms p95 | k6 |
| 4 | Checkout | `POST /api/loans` | < 500ms p95 | k6 |
| 5 | Renewal | `POST /api/loans/{id}/renew` | < 500ms p95 | k6 |
| 6 | My loans | `GET /api/loans` | < 500ms p95 | k6 |
| 7 | Admin stats | `GET /api/admin/stats` | < 500ms p95 | k6 |
| 8 | Reservation create | `POST /api/reservations` | < 500ms p95 | k6 |
| 9 | FTS with 1000 books | Various queries | < 200ms p95 | k6 |

### 6.2 Frontend Page Load Tests

| # | Test | Page | Target | Method |
|---|------|------|--------|--------|
| 10 | Homepage load (cold) | `/` | < 2s FCP | Playwright + Performance API |
| 11 | Homepage load (warm) | `/` (cached) | < 1s FCP | Playwright |
| 12 | Search results load | `/?q=fiction` | < 2s to visible results | Playwright |
| 13 | Book detail load | `/books/{id}` | < 2s FCP | Playwright |
| 14 | Loans page load | `/loans` | < 2s FCP | Playwright |
| 15 | Admin dashboard load | `/admin` | < 2s FCP | Playwright |

### 6.3 Database Query Performance

| # | Test | Query | Target |
|---|------|-------|--------|
| 16 | FTS query with GIN index | `plainto_tsquery('english', 'science fiction')` | < 50ms |
| 17 | Available copies count | Join books + book_copies with GROUP BY | < 100ms |
| 18 | User outstanding fines | SUM with status filter | < 50ms |
| 19 | Reservation queue query | ORDER BY queue_position | < 50ms |

---

## 7. Data Integrity Tests

These tests run against the seeded database to validate the seed data itself and cross-table consistency.

### 7.1 Seed Data Validation

| # | Test | Check | Expected |
|---|------|-------|----------|
| 1 | Book count | SELECT COUNT(*) FROM books | ~1000 |
| 2 | User count | SELECT COUNT(*) FROM users | 50 |
| 3 | Admin count | SELECT COUNT(*) FROM users WHERE role='admin' | 5 |
| 4 | Loan count | SELECT COUNT(*) FROM loans | ~500 |
| 5 | Active loan count | status='active' | ~75 |
| 6 | Overdue loan count | status='overdue' | ~25 |
| 7 | Returned loan count | status='returned' | ~400 |
| 8 | Reservation count | Total active | ~30 |
| 9 | Fine count | Total | ~40 |
| 10 | Review count | Total | ~200 |
| 11 | Staff picks count | is_staff_pick=true | 15-20 |

### 7.2 Referential Integrity

| # | Test | Check | Expected |
|---|------|-------|----------|
| 12 | Every loan has a valid user | loans.user_id IN users.id | 0 orphans |
| 13 | Every loan has a valid book_copy | loans.book_copy_id IN book_copies.id | 0 orphans |
| 14 | Every fine has a valid loan | fines.loan_id IN loans.id | 0 orphans |
| 15 | Every review has a valid user and book | reviews.user_id, reviews.book_id exist | 0 orphans |
| 16 | Every reservation has a valid user and book | reservations.user_id, reservations.book_id exist | 0 orphans |
| 17 | No duplicate reviews | UNIQUE(user_id, book_id) holds | 0 duplicates |

### 7.3 Rating Consistency

| # | Test | Check | Expected |
|---|------|-------|----------|
| 18 | avg_rating matches reviews | For every book: computed AVG(reviews.rating) = books.avg_rating | All match within 0.01 |
| 19 | rating_count matches reviews | For every book: COUNT(reviews) = books.rating_count | All match |
| 20 | avg_rating after insert | Insert a review, check book.avg_rating | Recalculated correctly by trigger |
| 21 | avg_rating after update | Update review rating, check book.avg_rating | Recalculated correctly |
| 22 | avg_rating after delete | Delete only review, check book.avg_rating | Resets to 0.00 |

### 7.4 Reservation Queue Consistency

| # | Test | Check | Expected |
|---|------|-------|----------|
| 23 | No gaps in queue_position | For each book, pending reservation positions form 1..N | No gaps |
| 24 | No duplicate positions | For each book, positions are unique | 0 duplicates |
| 25 | Atomic reorder after cancel | Cancel position 2, verify 3 becomes 2 | Consistent in single transaction |

### 7.5 Fine Calculation Accuracy

| # | Test | Check | Expected |
|---|------|-------|----------|
| 26 | Late return fine matches formula | For each fine: amount = min(days_overdue * daily_rate, 25.00) | All match |
| 27 | No fine for on-time returns | returned_at <= due_date implies no fine record | 0 false fines |
| 28 | Fine exists for every late return | returned_at > due_date implies fine record exists | 0 missing fines |

### 7.6 Copy Status Consistency

| # | Test | Check | Expected |
|---|------|-------|----------|
| 29 | Checked-out copies match active loans | COUNT(copies with status=checked_out) = COUNT(active+overdue loans) | Match |
| 30 | Reserved copies match ready reservations | COUNT(copies with status=reserved) = COUNT(ready reservations) | Match |
| 31 | No available copy has an active loan | No copy marked available has a non-returned loan | 0 inconsistencies |

---

## 8. Testing Tools and Setup

### 8.1 Recommended Tools

| Purpose | Tool | Version |
|---------|------|---------|
| Backend unit/integration | pytest + pytest-asyncio | Latest |
| Backend test client | httpx (AsyncClient with ASGITransport) | 0.27+ |
| Backend fixtures | pytest-factoryboy or custom factories | Latest |
| Backend coverage | pytest-cov | Latest |
| Frontend unit | vitest | Latest |
| Frontend component tests | @testing-library/react + @testing-library/jest-dom | Latest |
| Frontend hook tests | @testing-library/react-hooks (via renderHook) | Latest |
| E2E | Playwright | Latest |
| Performance/load | k6 | Latest |
| Mocking | unittest.mock (Python), msw (frontend) | Built-in / Latest |

### 8.2 Test Database Strategy

**Recommended: Neon Branch per test run**

```bash
# Create a test branch from the main Neon branch
neon branches create --name test-$(date +%s) --parent main

# Run migrations on the test branch
DATABASE_URL="$TEST_BRANCH_URL" alembic upgrade head

# Seed test data (smaller, deterministic subset)
DATABASE_URL="$TEST_BRANCH_URL" python -m app.seed.run_seed --test-mode

# Run tests
DATABASE_URL="$TEST_BRANCH_URL" pytest

# Delete branch after tests
neon branches delete test-...
```

**Alternative: Local PostgreSQL**

```bash
# Docker Compose for local test DB
docker run --name pageturn-test \
  -e POSTGRES_DB=pageturn_test \
  -e POSTGRES_USER=test \
  -e POSTGRES_PASSWORD=test \
  -p 5433:5432 \
  postgres:16

# Run migrations + seed + tests against localhost:5433
```

**Test data fixtures**: Use a smaller, deterministic seed for tests:
- 20 books (covering all item types and genres)
- 5 users (1 admin, 4 regular with varying fine levels)
- 30 loans (10 active, 5 overdue, 15 returned)
- 5 reservations (2 pending, 2 ready, 1 fulfilled)
- 10 fines (5 pending, 3 paid, 2 waived)
- 15 reviews

### 8.3 CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r api/requirements.txt -r api/requirements-test.txt
      - run: cd api && pytest tests/unit/ --cov=app --cov-report=xml -v
      - uses: codecov/codecov-action@v4

  backend-integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: pageturn_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/pageturn_test
      CLERK_SECRET_KEY: test_secret
      CLERK_WEBHOOK_SECRET: test_webhook_secret
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r api/requirements.txt -r api/requirements-test.txt
      - run: cd api && alembic upgrade head
      - run: cd api && python -m app.seed.run_seed --test-mode
      - run: cd api && pytest tests/integration/ --cov=app --cov-report=xml -v

  frontend-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npx vitest run --coverage

  e2e:
    runs-on: ubuntu-latest
    needs: [backend-integration, frontend-unit]
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: pageturn_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/pageturn_test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: pip install -r api/requirements.txt
      - run: cd api && alembic upgrade head && python -m app.seed.run_seed --test-mode
      - run: cd api && uvicorn app.main:app --port 8000 &
      - run: cd frontend && npm ci && npm run build && npx serve dist -l 5173 &
      - run: npx playwright install --with-deps chromium
      - run: cd frontend && npx playwright test

  mcp:
    runs-on: ubuntu-latest
    needs: [backend-integration]
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: pageturn_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/pageturn_test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r mcp/requirements.txt -r mcp/requirements-test.txt
      - run: cd api && alembic upgrade head && python -m app.seed.run_seed --test-mode
      - run: cd mcp && pytest tests/ -v
```

### 8.4 Test Configuration Files

**`api/pytest.ini`**:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    unit: Unit tests (no DB)
    integration: Integration tests (requires DB)
    slow: Tests that take > 5 seconds
```

**`frontend/vitest.config.ts`**:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    coverage: {
      reporter: ['text', 'lcov'],
      include: ['src/**/*.ts', 'src/**/*.tsx'],
      exclude: ['src/test-setup.ts', 'src/**/*.test.*'],
    },
  },
});
```

**`frontend/playwright.config.ts`**:
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
  webServer: [
    {
      command: 'cd ../api && uvicorn app.main:app --port 8000',
      port: 8000,
      reuseExistingServer: true,
    },
    {
      command: 'npm run dev',
      port: 5173,
      reuseExistingServer: true,
    },
  ],
});
```

---

## 9. Test Matrix

### 9.1 Feature x Test Type Coverage

| Feature | Unit | Integration | E2E | Performance | Data Integrity |
|---------|:----:|:-----------:|:---:|:-----------:|:--------------:|
| F1: Book Search & Browse | S1.4 (4 tests) | S3.1.1 (13 tests) | Flow 1 | P1-P2, P9, P16-P17 | -- |
| F2: Book Detail | -- | S3.1.1 #10-11 | Flow 1 | P13 | -- |
| F3: User Auth | -- | S3.1.2 (5 tests), S3.3 (6 tests) | Flow 2 | -- | -- |
| F4: Book Checkout | S2.1.2 #1-5 | S3.1.3 #19-28 | Flow 2, Flow 3, Flow 7 | P4 | D29-D31 |
| F5: Loan Management | S2.1.2 #6-13 | S3.1.3 #29-38 | Flow 4, Flow 5 | P5-P6 | -- |
| F6: Reservations | S2.1.3 (10 tests) | S3.1.4 (8 tests) | Flow 3, Flow 5, Flow 10 | P8 | D23-D25 |
| F7: Reviews & Ratings | -- | S3.1.6 (9 tests) | Flow 6 | -- | D18-D22 |
| F8: Fines & Dues | S2.1.1 (15 tests) | S3.1.5 (3 tests), S3.1.13 (3 tests) | Flow 7, Flow 9 | -- | D26-D28 |
| F9: Admin Books | -- | S3.1.10 (10 tests) | Flow 8 | -- | -- |
| F10: Admin Users | -- | S3.1.11 (6 tests) | Flow 9 | -- | -- |
| F11: Admin Dashboard | -- | S3.1.14 (1 test) | -- | P15 | -- |
| F12: AI Assistant | S2.1.5 (6 tests) | S3.1.7 (6 tests) | -- | -- | -- |
| F13: MCP User Tools | -- | S5.2 (20 tests) | -- | -- | -- |
| F14: MCP Admin Tools | -- | S5.3 (10 tests) | -- | -- | -- |
| F15: Staff Picks | -- | S3.1.1 #6 | Flow 1 | -- | D11 |
| F16: Top Rated | -- | S3.1.1 #7 | Flow 1 | -- | -- |
| Cron: Overdue | -- | S3.4 #115-117 | -- | -- | -- |
| Cron: Reservation Expiry | -- | S3.4 #118-122 | -- | -- | -- |

### 9.2 Implementation Priority Order

Build tests in this order to maximize coverage of the highest-risk areas first:

| Priority | Tests | Rationale |
|----------|-------|-----------|
| **P0** | Backend unit: fine_service, loan_service | Core business rules, highest bug risk |
| **P0** | Backend integration: checkout flow (6 preconditions) | Most complex endpoint, most error paths |
| **P0** | Backend integration: reservation queue + return trigger | Concurrency-sensitive, atomic operations |
| **P1** | Backend integration: all remaining API endpoints | Full API coverage |
| **P1** | Frontend unit: utility functions, hooks | Catch logic bugs before E2E |
| **P1** | Data integrity: seed validation, rating consistency | Ensure demo is credible |
| **P1** | Cron job tests | Silent failures are hard to debug |
| **P2** | E2E: Flows 1-3, 7 (core user paths) | Catch cross-page regressions |
| **P2** | MCP: auth + tool coverage | Ensure AI assistant works |
| **P2** | Frontend component tests | Catch rendering bugs |
| **P3** | E2E: Flows 4-6, 8-10 (remaining flows) | Secondary paths |
| **P3** | Performance tests | Validate NFRs |
| **P3** | Responsive design tests | Visual correctness |

---

## 10. Acceptance Test Checklist

Every PRD acceptance criterion mapped to a test. Columns indicate whether the test can be automated (A) or requires manual verification (M).

### F1: Book Search & Browse

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Search bar on homepage accepts free-text queries | E2E Flow 1 step 6 | A |
| 2 | Results match title (highest weight), author, description, genre | Unit S2.1.4 #1-4 | A |
| 3 | Results return within 200ms | Perf P1, P9 | A |
| 4 | Result card shows: cover, title, author, avg rating, genre, availability | E2E Flow 1 step 7 (assert elements) | A |
| 5 | Filter by genre (multi-select) | Integration S3.1.1 #3; E2E Flow 1 step 9 | A |
| 6 | Filter by item type | Integration S3.1.1 #4 | A |
| 7 | Filter by availability | Integration S3.1.1 #5 | A |
| 8 | Sort by relevance, title, rating, year | Integration S3.1.1 #7; Unit S2.1.4 #9-10 | A |
| 9 | Pagination: 20 per page | Integration S3.1.1 #8 | A |
| 10 | Empty state: "No books found" | Integration S3.1.1 #9; E2E (search for nonsense) | A |
| 11 | No authentication required | Integration S3.1.1 #1 (no auth header) | A |

### F2: Book Detail Page

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Displays full metadata (cover, title, author, ISBN, year, pages, publisher, language, description, genres, type) | E2E Flow 1 step 12 (assert elements) | A |
| 2 | Average rating as stars with count | E2E component: assert star rating + count text | A |
| 3 | Availability section (available/checked out/user has it) | Integration S3.1.1 #10 (response shape); E2E Flow 2 step 5 | A |
| 4 | Author name links to filtered search | E2E: click author link, verify URL contains author param | A |
| 5 | Reviews section below metadata | E2E Flow 1 step 13 | A |
| 6 | "More by Author" section | E2E Flow 1 step 14 | A |
| 7 | Breadcrumb navigation (contextual) | E2E: navigate from search, verify breadcrumb text | A |
| 8 | No auth required for viewing; buttons redirect to sign-in | E2E Flow 2 steps 1-3 | A |

### F3: User Authentication

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | "Sign In" button opens Clerk sign-in | E2E Flow 2 step 2 | M |
| 2 | Supports Google SSO, email + password, magic link | Manual (Clerk config verification) | M |
| 3 | User synced via webhook on sign-in | Integration S3.3 #109 | A |
| 4 | Nav bar shows avatar, name, dropdown | E2E: assert signed-in nav state | A |
| 5 | Dropdown links (My Loans, History, Fines, Reviews, AI, Sign Out) | E2E: assert dropdown content | A |
| 6 | Admin sees "Admin" link | E2E: sign in as admin, check dropdown | A |
| 7 | Session persists across reload | E2E: sign in, reload, assert still signed in | A |
| 8 | Sign out clears session and redirects | E2E: sign out, assert redirect to homepage | A |

### F4: Book Checkout

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | "Check Out" button visible when available | E2E Flow 2 step 1 | A |
| 2 | Verify authenticated | Integration S3.1.2 #17-18 | A |
| 3 | Verify no checkout block (fines >= $10) | Integration S3.1.3 #21; E2E Flow 7 | A |
| 4 | Verify max loans not exceeded | Integration S3.1.3 #22 | A |
| 5 | Find available copy, create loan | Integration S3.1.3 #19 | A |
| 6 | Success banner with due date | E2E Flow 2 steps 5-6 | A |
| 7 | No copies: auto-reserve with queue position | Integration S3.1.3 #20; E2E Flow 3 | A |
| 8 | Fines block: coral banner + disabled button | E2E Flow 7 steps 9-10 | A |
| 9 | Max loans: coral banner + disabled button | E2E (set up user at max, attempt checkout) | A |
| 10 | Fulfills reservation if ready | Integration S3.1.3 #25 | A |
| 11 | Auto-selects copy (user does not choose) | Integration S3.1.3 #19 (no copy_id in request) | A |
| 12 | Loan periods by item type (book 14d, dvd 7d, audiobook 21d) | Integration S3.1.3 #26-28; Unit S2.1.2 #1-5 | A |

### F5: Loan Management

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Table of active loans with all fields | E2E Flow 2 step 9; E2E Flow 4 step 1 | A |
| 2 | "Renew" button per loan | E2E Flow 4 step 2 | A |
| 3 | "Return" info text | E2E: assert info banner text | A |
| 4 | Overdue visual indicator | E2E Flow 7 step 4 | A |
| 5 | Empty state | E2E: new user with no loans, assert empty message | A |
| 6 | History page with past loans | E2E Flow 6 step 9 (navigate to history) | A |
| 7 | Pagination on history | Integration S3.1.3 #33 | A |
| 8 | Max 2 renewals | Integration S3.1.3 #35; Unit S2.1.2 #8 | A |
| 9 | Renewal extends by original period from current date | Unit S2.1.2 #6 | A |
| 10 | Renewal blocked if reservation exists | Integration S3.1.3 #36; E2E Flow 5 | A |
| 11 | Renewal blocked if overdue > 7 days | Integration S3.1.3 #37; Unit S2.1.2 #10 | A |
| 12 | Review nudge for recent unreviewed return | E2E: verify nudge card appears for recent return | A |
| 13 | Nudge dismissible (stored in localStorage) | E2E: dismiss, reload, verify not shown | A |
| 14 | Currently Reading section on homepage | E2E: sign in with loans, verify section | A |

### F6: Reservation System

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Immediate reserve when available | Integration S3.1.4 #39; Unit S2.1.3 #6 | A |
| 2 | Waitlist when unavailable | Integration S3.1.4 #40; Unit S2.1.3 #7 | A |
| 3 | Return triggers next-in-queue | Integration S3.1.12 #92; Unit S2.1.3 #8 | A |
| 4 | Expiry cron works | Integration S3.4 #118-119 | A |
| 5 | Queue reorder on cancel (atomic) | Integration S3.1.4 #44; Unit S2.1.3 #2-5; Data D23-D25 | A |
| 6 | My Reservations list | E2E Flow 3 step 5-6 | A |
| 7 | Cancel button | E2E Flow 3 step 7 | A |
| 8 | Ready reservation alert banner | E2E Flow 10 step 9 | A |
| 9 | Coral notification dot on nav | E2E: verify dot present when reservation ready | A |
| 10 | Renewal blocking when reservation pending | Integration S3.1.3 #36; E2E Flow 5 | A |

### F7: Reviews & Ratings

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Reviews section on book detail | E2E Flow 1 step 13 | A |
| 2 | Each review shows avatar, name, rating, date, text | E2E Flow 6 step 7 | A |
| 3 | Sorted by most recent | Integration S3.1.1 #12 | A |
| 4 | Average rating computed and displayed | Data D18-D19; E2E Flow 6 step 8 | A |
| 5 | "Write a Review" for eligible users | E2E Flow 6 step 3 | A |
| 6 | Review form: star selector + text area | E2E Flow 6 steps 4-5 | A |
| 7 | One review per user per book | Integration S3.1.6 #51; Data D17 | A |
| 8 | Edit and delete own review | E2E Flow 6 steps 11-13; Integration S3.1.6 #57-58 | A |
| 9 | Avg recalculation on submit/update/delete | Data D20-D22; Integration (insert review, check book.avg_rating) | A |
| 10 | My Reviews page | E2E Flow 6 step 9 | A |

### F8: Fines & Dues

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Fine list with all fields | E2E Flow 7 step 5 | A |
| 2 | Total outstanding prominently displayed | E2E Flow 7 step 5 (stat cards) | A |
| 3 | Warning banner when >= $10 | E2E Flow 7 step 6 | A |
| 4 | Fines accrue day after due date | Unit S2.1.1 #1-2 | A |
| 5 | Daily rates by item type | Unit S2.1.1 #3-6, #9 | A |
| 6 | Max fine $25 per item | Unit S2.1.1 #7-8 | A |
| 7 | Fine on late return | Integration S3.1.12 #91 | A |
| 8 | Cron detects overdue + recalculates | Integration S3.4 #115-117 | A |
| 9 | Display calculated fine for active overdue | Integration S3.1.3 #30 | A |
| 10 | Lost item fee ($30 or replacement cost) | Unit S2.1.1 #11-12; Integration S3.1.12 #93 | A |
| 11 | Admin: view all fines | Integration S3.1.13 #95-96 | A |
| 12 | Admin: waive fine | Integration S3.1.13 #97; E2E Flow 9 | A |

### F9: Admin Book Management

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Searchable book table | E2E Flow 8 step 2 | A |
| 2 | "Add Book" with form | E2E Flow 8 steps 3-5 | A |
| 3 | Edit book | E2E Flow 8 steps 9-12 | A |
| 4 | Delete book with confirmation | E2E Flow 8 steps 14-17 | A |
| 5 | "Add Copies" per book | Integration S3.1.10 #79 | A |
| 6 | View/manage copies in modal | E2E Flow 8 steps 7-8 | A |
| 7 | Validation: title and author required | Integration S3.1.10 #73-74 | A |

### F10: Admin User Management

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Searchable user table | Integration S3.1.11 #82-83; E2E Flow 9 step 3 | A |
| 2 | User detail view | Integration S3.1.11 #84; E2E Flow 9 step 5 | A |
| 3 | Edit max_loans, role | Integration S3.1.11 #85-87 | A |
| 4 | Promote/demote with Clerk sync | Integration S3.1.11 #86-87 | A |

### F11: Admin Dashboard

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Stat cards with correct counts | Integration S3.1.14 #98 | A |
| 2 | Quick action buttons | E2E: verify buttons exist and navigate | A |

### F12: AI Assistant

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Setup guide with steps | E2E or manual: verify page content | M |
| 2 | "Copy Config" button | Manual: click, verify clipboard | M |
| 3 | API key list with fields | Integration S3.1.7 #62 | A |
| 4 | Generate new key flow | Integration S3.1.7 #59-61 | A |
| 5 | Show key once with warning | Manual: verify modal behavior | M |
| 6 | Revoke key | Integration S3.1.7 #63 | A |

### F13: MCP User Tools (13 tools)

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | All 13 user tools callable | MCP S5.2 #8-27 | A |
| 2 | Tools return correct data | MCP S5.2 (each test validates response shape) | A |
| 3 | Auth enforced | MCP S5.1 #1-7 | A |

### F14: MCP Admin Tools (9 tools)

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | All 9 admin tools callable | MCP S5.3 #28-37 | A |
| 2 | Scope enforcement | MCP S5.4 #38-40 | A |

### F15: Staff Picks

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Books marked as staff picks | Data D11 | A |
| 2 | Optional note per pick | Seed data validation | A |
| 3 | Hero section shows staff pick | E2E Flow 1 step 2 | A |
| 4 | Staff Picks section on homepage | E2E Flow 1 step 3 | A |
| 5 | Filterable via API | Integration S3.1.1 #6 | A |

### F16: Top Rated

| # | Criterion | Test Reference | A/M |
|---|-----------|---------------|-----|
| 1 | Top Rated section on homepage | E2E Flow 1 step 3 (verify section) | A |
| 2 | Sorted by avg_rating DESC | Integration S3.1.1 #7 | A |
| 3 | Minimum 3 ratings to qualify | Integration: create book with 2 reviews, verify excluded from sort=rating | A |

### Summary

| Category | Automated | Manual | Total |
|----------|:---------:|:------:|:-----:|
| F1-F16 acceptance criteria | 88 | 6 | 94 |

The 6 manual tests are all related to Clerk SSO flows (Google sign-in, magic link) and clipboard/modal UX interactions that are impractical to fully automate.

---

## Appendix: Test File Structure

```
api/
  tests/
    conftest.py              # Shared fixtures (db session, test client, auth helpers)
    factories.py             # Factory functions for test data
    unit/
      test_fine_service.py
      test_loan_service.py
      test_reservation_service.py
      test_search_service.py
      test_api_key_service.py
    integration/
      test_books_api.py
      test_loans_api.py
      test_reservations_api.py
      test_fines_api.py
      test_reviews_api.py
      test_users_api.py
      test_api_keys_api.py
      test_webhooks.py
      test_cron.py
      test_admin_api.py
      test_db_triggers.py
    data_integrity/
      test_seed_validation.py
      test_referential_integrity.py
      test_rating_consistency.py
      test_reservation_queue.py
      test_fine_accuracy.py
      test_copy_status.py
  requirements-test.txt      # pytest, pytest-asyncio, pytest-cov, httpx, factory-boy

frontend/
  src/
    __tests__/
      utils.test.ts
      hooks/
        useBooks.test.ts
        useLoans.test.ts
      components/
        StarRating.test.tsx
        AvailabilityBadge.test.tsx
        BookCard.test.tsx
        Pagination.test.tsx
        Modal.test.tsx
        ProtectedRoute.test.tsx
    test-setup.ts            # jsdom setup, MSW handlers
  e2e/
    fixtures/
      auth.ts                # Clerk auth helpers (cookie injection)
    flows/
      book-discovery.spec.ts
      checkout.spec.ts
      auto-reservation.spec.ts
      renewal.spec.ts
      renewal-blocked.spec.ts
      reviews.spec.ts
      fines-block.spec.ts
      admin-books.spec.ts
      admin-users.spec.ts
      admin-return.spec.ts
    responsive/
      mobile.spec.ts

mcp/
  tests/
    conftest.py
    test_auth.py
    test_user_tools.py
    test_admin_tools.py
    test_scope.py
```
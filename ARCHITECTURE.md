# PageTurn — Library Catalogue & Management System

## Architecture Plan v1.0

---

# PART 1: NON-TECHNICAL OVERVIEW

## What Is PageTurn?

PageTurn is a modern, full-featured library catalogue website where users can browse books, manage loans, and get AI-powered recommendations — all from their browser. Administrators get a powerful dashboard to manage the entire library.

---

## Feature Overview (What Users Will Experience)

### For Anyone (No Account Needed)
- **Search the Catalogue**: Search 1,000+ books by title, author, genre, or item type (book, audiobook, DVD, etc.). Results are instant thanks to indexed search.
- **View Book Details**: See cover art, description, author info, page count, publication year, ISBN, and average rating from community reviews.
- **Read Reviews**: Browse public ratings and reviews left by library members.
- **Check Availability**: See at a glance whether a book is available, checked out (with expected return date), or has a waitlist.

### For Logged-In Members
- **One-Click SSO Login**: Sign in with Google, GitHub, or email — powered by Clerk. No separate library card needed.
- **Check Out Books**: Reserve an available book instantly. If it's checked out, join the waitlist — you'll be next in line when it's returned.
- **My Loans Dashboard**: See all your current loans, due dates, and renewal options in one place.
- **Renew Loans**: Extend your loan period with one click — unless someone else is waiting for the book.
- **Loan History**: Browse your complete borrowing history.
- **Fines & Dues**: See any outstanding fines for late returns. Pay or dispute them.
- **Rate & Review Books**: Leave a star rating (1-5) and written review for any book you've borrowed.
- **AI Library Assistant (MCP)**: Connect an AI agent (like Claude) to your library account. The agent can search books, check your loans, make recommendations based on your reading history and reviews, and even check out books for you.

### For Administrators
- **Book Management**: Add, edit, and delete books with full metadata (title, author, ISBN, genre, description, cover image, item type, page count, publication year).
- **User Management**: View all users, edit profiles, manage their loans and reservations on their behalf.
- **Fine Management**: View all outstanding fines. Waive fines for individual users or in bulk.
- **Admin AI Assistant (MCP)**: A separate, more powerful AI agent connection. Can perform all admin operations — manage books, look up users, waive fines, generate reports.

---

## User Stories

### US-1: Casual Browser
> "As a visitor, I want to search for books without creating an account, so I can see what the library has before committing."

### US-2: New Member
> "As a new user, I want to sign up with my Google account and immediately check out a book I found."

### US-3: Active Reader
> "As a member, I want to see all my current loans, renew the ones I haven't finished, and check my reading history."

### US-4: Waitlister
> "As a member, I want to reserve a book that's currently checked out, so I'm next in line when it's returned."

### US-5: Reviewer
> "As a member who just finished a book, I want to leave a rating and review so others know if it's worth reading."

### US-6: Late Returner
> "As a member with overdue books, I want to see my fines clearly and understand how they're calculated."

### US-7: AI-Assisted Reader
> "As a member, I want to connect my library account to an AI assistant that knows my reading history and can recommend my next read."

### US-8: Librarian (Admin)
> "As an admin, I want to add new books to the catalogue, manage user accounts, and waive fines when appropriate."

### US-9: Admin with AI
> "As an admin, I want an AI assistant that can quickly look up user accounts, check overdue books, and perform bulk operations."

---

## User Flow (Loom-Friendly Walkthrough Script)

**Target length**: ~6-7 minutes total.

### Scene 1: Homepage Browse & Search (0:00 - 1:00)
1. Open the homepage — show the Staff Pick hero section with the featured book, tilted cover, gradient glow, and "Check Out" CTA
2. (If logged in) Show the "Currently Reading" section above Staff Picks — active loans as scroll cards with due date badges
3. Scroll down through the accordion genre sections — expand "Fiction", show the horizontal scroll cards with covers, ratings, and "2 of 3 copies available" callouts
3. Point out the item type badges on non-book items (audiobook, DVD)
4. Type "science fiction" into the nav search bar → page transitions to search results grid
5. Results appear instantly — book cards with covers, titles, authors, ratings
6. Click a book card → detail page with full metadata, availability badge, reviews

### Scene 2: Sign Up & Check Out (1:00 - 1:45)
1. Click "Check Out" on an available book → redirected to sign in
2. Click "Continue with Google" → Clerk SSO flow → redirected back
3. Book is now checked out — inline green success banner replaces action buttons with due date and "View My Loans →" link
4. Navigate to "My Loans" — see the book listed with due date and renew button

### Scene 3: Reservations & Renewal Blocking (1:45 - 2:35)
1. Search for a popular book that's currently checked out
2. Book detail page shows "Checked Out — Returns Apr 15" with a "Reserve" button
3. Click Reserve → confirmation: "You're #1 in the waitlist. We'll notify you when it's available."
3b. Navigate to "My Loans" — show the ready-reservation alert banner at the top of the page
4. Switch to a pre-logged-in browser tab as a different user (the user who has this book checked out)
5. Show their "My Loans" page — their renew button is disabled with message: "Cannot renew — another member is waiting for this book". Explain WHY renewal is blocked (protects waitlisted users).

### Scene 4: Loan History & Reviews (2:35 - 3:15)
1. Click "History" in the sub-nav → see past loans grouped by month (March 2026, February 2026, etc.)
2. Click "Write Review" on a returned book
3. Leave a 4-star rating and a short review
4. Navigate to the book's public page → see the review appear with the community average

### Scene 5: Fines Dashboard (3:15 - 3:45)
1. Show a user with an overdue book (mock data)
2. Navigate to "Fines & Dues" — see the stat cards (Outstanding, Paid, Waived)
3. Show the calculated fine amount with the breakdown (e.g., "14 days × $0.25/day = $3.50")

### Scene 6: Admin Panel (3:45 - 4:35)
1. Log in as admin → admin dashboard with stats (total books, active loans, overdue count)
2. Add a new book — fill in metadata form, specify copies and condition
3. Search for a user → view their loans → waive a fine
4. Edit a book's metadata → changes reflect immediately on the public catalogue
5. (**Note**: Admin page mockups must be completed before recording this scene — see UI_HANDOFF.md)

### Scene 7: AI Assistant Demo (4:35 - 5:35)
1. Show the AI Assistant page — walk through the setup guide, click "Copy Config", show example prompts
2. Show Claude Desktop with the library MCP connected
2. Ask: "What books do I have checked out?" → agent calls the MCP, returns loan list
3. Ask: "Based on my reading history, what should I read next?" → agent analyzes past loans and reviews, searches the catalogue, recommends books
4. Ask: "Check out 'Project Hail Mary' for me" → agent makes the reservation through the MCP
5. (Admin demo) Ask: "Show me all users with overdue books" → agent returns the list with fine amounts

---

# PART 2: TECHNICAL ARCHITECTURE

## Tech Stack

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | React 18 + TypeScript + Vite | Vercel |
| Backend API | Python 3.12 + FastAPI | Vercel Serverless Functions |
| Database | PostgreSQL 16 | Neon (serverless Postgres) |
| Authentication | Clerk | Clerk Cloud |
| Search | PostgreSQL Full-Text Search + GIN indexes | Neon |
| MCP Servers | Python + `mcp` SDK | Google Cloud Run |
| File Storage | Clerk (avatars) / Open Library (covers) | External |

### Why These Choices
- **FastAPI on Vercel**: Python serverless functions with automatic scaling. FastAPI gives us auto-generated OpenAPI docs, Pydantic validation, and async support.
- **Neon PostgreSQL**: Serverless Postgres that scales to zero — perfect for Vercel. Branching for dev/staging. Generous free tier (0.5 GB storage, 190 compute hours/mo).
- **Clerk**: Best-in-class auth with React SDK, Python backend SDK, webhook support. Free tier covers 10K MAU. User metadata for role management (admin/user).
- **PostgreSQL FTS**: No need for Elasticsearch for 1,000 books. GIN indexes on tsvector columns give us sub-millisecond search with ranking.

---

## Project Structure

```
pageturn/
├── ARCHITECTURE.md              # This file
├── frontend/                    # React TypeScript app
│   ├── FRONTEND.md              # Frontend architecture details
│   ├── package.json
│   ├── vite.config.ts
│   ├── vercel.json
│   ├── public/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── routes/
│   │   │   ├── index.tsx        # Home / search
│   │   │   ├── book.$id.tsx     # Book detail
│   │   │   ├── loans.tsx        # My loans
│   │   │   ├── history.tsx      # Loan history
│   │   │   ├── fines.tsx        # Fines & dues
│   │   │   ├── admin/
│   │   │   │   ├── index.tsx    # Admin dashboard
│   │   │   │   ├── books.tsx    # Manage books
│   │   │   │   ├── users.tsx    # Manage users
│   │   │   │   └── fines.tsx    # Manage fines
│   │   │   └── auth/
│   │   │       └── callback.tsx # Clerk callback
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── BookCard.tsx
│   │   │   ├── BookDetail.tsx
│   │   │   ├── LoanCard.tsx
│   │   │   ├── ReviewForm.tsx
│   │   │   ├── ReviewList.tsx
│   │   │   ├── FineCard.tsx
│   │   │   ├── ReservationButton.tsx
│   │   │   ├── AdminLayout.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── hooks/
│   │   │   ├── useBooks.ts
│   │   │   ├── useLoans.ts
│   │   │   ├── useFines.ts
│   │   │   └── useReviews.ts
│   │   ├── lib/
│   │   │   ├── api.ts           # API client (fetch wrapper)
│   │   │   └── clerk.ts         # Clerk config
│   │   └── types/
│   │       └── index.ts         # Shared TypeScript types
│   └── tsconfig.json
│
├── api/                         # FastAPI backend (Vercel serverless)
│   ├── API.md                   # Backend architecture details
│   ├── requirements.txt
│   ├── vercel.json
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, middleware
│   │   ├── config.py            # Environment config
│   │   ├── database.py          # Neon connection, SQLAlchemy engine
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── book.py          # Book, BookCopy models
│   │   │   ├── user.py          # User model (synced from Clerk)
│   │   │   ├── loan.py          # Loan model
│   │   │   ├── reservation.py   # Reservation model
│   │   │   ├── fine.py          # Fine model
│   │   │   ├── review.py        # Review/Rating model
│   │   │   └── api_key.py       # API key model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── book.py          # Pydantic schemas for books
│   │   │   ├── loan.py
│   │   │   ├── reservation.py
│   │   │   ├── fine.py
│   │   │   ├── review.py
│   │   │   └── user.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── books.py         # /api/books - public search + admin CRUD
│   │   │   ├── loans.py         # /api/loans - checkout, renew, return
│   │   │   ├── reservations.py  # /api/reservations - reserve, cancel
│   │   │   ├── fines.py         # /api/fines - view, waive (admin)
│   │   │   ├── reviews.py       # /api/reviews - CRUD reviews
│   │   │   ├── users.py         # /api/users - admin user management
│   │   │   └── api_keys.py      # /api/api-keys - generate/revoke keys
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── book_service.py
│   │   │   ├── loan_service.py  # Business logic for loans
│   │   │   ├── reservation_service.py
│   │   │   ├── fine_service.py  # Fine calculation logic
│   │   │   └── search_service.py # Full-text search logic
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── clerk.py         # Clerk JWT verification
│   │   │   └── dependencies.py  # FastAPI dependencies (get_current_user, require_admin)
│   │   └── seed/
│   │       ├── __init__.py
│   │       ├── seed_books.py    # Fetch from Open Library + seed DB
│   │       ├── seed_users.py    # Generate mock users
│   │       ├── seed_loans.py    # Generate mock loan history
│   │       ├── seed_fines.py    # Generate mock fines
│   │       ├── seed_reviews.py  # Generate mock reviews
│   │       └── run_seed.py      # Orchestrator: seed everything
│   └── alembic/                 # Database migrations
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
│
├── mcp/                         # MCP servers (Google Cloud Run)
│   ├── MCP.md                   # MCP architecture details
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── user_server.py           # User-facing MCP server
│   ├── admin_server.py          # Admin-facing MCP server
│   ├── auth.py                  # API key validation
│   └── tools/
│       ├── __init__.py
│       ├── search.py            # search_books tool
│       ├── loans.py             # get_loans, checkout, renew, return tools
│       ├── reservations.py      # reserve_book, cancel_reservation tools
│       ├── reviews.py           # get_my_reviews, get_book_reviews tools
│       ├── fines.py             # get_fines tool (user), waive_fine (admin)
│       ├── users.py             # Admin user management tools
│       └── books_admin.py       # Admin book CRUD tools
│
├── scripts/
│   ├── setup_neon.py            # Create Neon database + run migrations
│   ├── generate_api_key.py      # CLI to generate MCP API keys
│   └── promote_admin.py         # CLI to promote a user to admin
│
└── tasks/
    └── todo.md                  # Implementation tracking
```

---

## Database Schema

### Entity Relationship Diagram (Text)

```
users 1──∞ loans ∞──1 book_copies ∞──1 books
users 1──∞ reservations ∞──1 books
users 1──∞ fines ∞──1 loans
users 1──∞ reviews ∞──1 books
users 1──∞ api_keys
```

### Table Definitions

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, default gen_random_uuid() |
| clerk_id | VARCHAR(255) | Unique, from Clerk webhook |
| email | VARCHAR(255) | Unique |
| first_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| role | VARCHAR(20) | 'user' or 'admin', default 'user' |
| max_loans | INT | Default 5 |
| deleted_at | TIMESTAMPTZ | Set on user.deleted webhook; preserves loan/fine/review records |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Admin Promotion Strategy**: Use a CLI script (`scripts/promote_admin.py`) that takes an email and sets `role='admin'`. Alternatively, admins can promote other users via the admin panel. The first admin is seeded or promoted via CLI. Clerk's `publicMetadata.role` is also synced so the frontend can check role without an API call.

#### `books`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| title | VARCHAR(500) | |
| author | VARCHAR(500) | |
| isbn | VARCHAR(20) | Unique, nullable |
| isbn13 | VARCHAR(20) | Unique, nullable |
| description | TEXT | |
| genre | VARCHAR(100) | Primary genre |
| genres | TEXT[] | Array of all genres |
| item_type | VARCHAR(50) | 'book', 'audiobook', 'dvd', 'ebook', 'magazine' |
| cover_image_url | VARCHAR(1000) | URL to cover image |
| page_count | INT | Nullable |
| publication_year | INT | |
| publisher | VARCHAR(500) | |
| language | VARCHAR(10) | Default 'en' |
| avg_rating | DECIMAL(3,2) | Denormalized, updated on review changes |
| rating_count | INT | Denormalized |
| search_vector | TSVECTOR | Auto-populated GIN index for FTS |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**Search Index**: A GIN index on `search_vector`, populated via trigger:
```sql
search_vector = setweight(to_tsvector('english', title), 'A') ||
                setweight(to_tsvector('english', author), 'B') ||
                setweight(to_tsvector('english', coalesce(description, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(genre, '')), 'D')
```

#### `book_copies`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| book_id | UUID | FK → books.id |
| barcode | VARCHAR(50) | Unique identifier for physical copy |
| condition | VARCHAR(20) | 'new', 'good', 'fair', 'poor' |
| status | VARCHAR(20) | 'available', 'checked_out', 'reserved', 'damaged', 'lost' |
| added_at | TIMESTAMPTZ | |

**Note**: Each `book` can have multiple `book_copies`. This models a real library where you might have 3 copies of a popular book. Availability is determined by whether any copy has status='available'.

#### `loans`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| book_copy_id | UUID | FK → book_copies.id |
| checked_out_at | TIMESTAMPTZ | |
| due_date | TIMESTAMPTZ | |
| returned_at | TIMESTAMPTZ | Null if still active |
| renewed_count | INT | Default 0 |
| status | VARCHAR(20) | 'active', 'returned', 'overdue' |

#### `reservations`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| book_id | UUID | FK → books.id (not copy — any copy will do) |
| reserved_at | TIMESTAMPTZ | |
| expires_at | TIMESTAMPTZ | Reservation expires if not picked up |
| status | VARCHAR(20) | 'pending', 'ready', 'fulfilled', 'expired', 'cancelled' |
| queue_position | INT | Position in waitlist (1 = next) |
| notified_at | TIMESTAMPTZ | When user was notified book is available |

#### `fines`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| loan_id | UUID | FK → loans.id |
| amount | DECIMAL(10,2) | Total fine amount |
| reason | VARCHAR(100) | 'late_return', 'lost_item', 'damaged_item' |
| status | VARCHAR(20) | 'pending', 'paid', 'waived' |
| paid_at | TIMESTAMPTZ | When payment was recorded |
| waived_by | UUID | FK → users.id (admin who waived) |
| waived_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

#### `reviews`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| book_id | UUID | FK → books.id |
| rating | INT | 1-5 stars |
| review_text | TEXT | Optional written review |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| UNIQUE(user_id, book_id) | | One review per user per book |

#### `api_keys`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| key_hash | VARCHAR(255) | SHA-256 hash of the API key |
| key_prefix | VARCHAR(10) | First 8 chars for identification (e.g., "pt_usr_3f") |
| scope | VARCHAR(20) | 'user' or 'admin' |
| name | VARCHAR(100) | User-given name like "Claude Desktop" |
| last_used_at | TIMESTAMPTZ | |
| expires_at | TIMESTAMPTZ | Nullable |
| revoked_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

**API Key Generation**: Keys follow the format `pt_usr_<32-random-hex>` (user) or `pt_adm_<32-random-hex>` (admin). Only the hash is stored. The plaintext key is shown once at creation time. This is the standard approach used by Stripe, OpenAI, etc.

---

## Business Logic

### Loan Rules
| Rule | Value | Notes |
|------|-------|-------|
| Default loan period | 14 days | Books, ebooks |
| Short loan period | 7 days | DVDs, magazines |
| Audiobook loan period | 21 days | Audiobooks |
| Max renewals | 2 | Per loan |
| Max concurrent loans | 5 | Per user (configurable per user by admin) |
| Renewal extension | Same as original period | Resets from current date |
| Renewal blocked if | Reservation exists for the book | Protects waitlisted users |

### Fine Rules
| Rule | Value |
|------|-------|
| Late fee (books/ebooks) | $0.25/day |
| Late fee (DVDs) | $1.00/day |
| Late fee (audiobooks) | $0.50/day |
| Late fee (magazines) | $0.10/day |
| Max fine per item | $25.00 (cap) |
| Lost item fee | Replacement cost (stored in book metadata) or $30 default |
| Fine blocks checkout | Yes, if total unpaid fines >= $10.00 |

### Fine Calculation
- Fines accrue daily starting the day after the due date
- Fines are calculated on-the-fly (not stored until the book is returned or marked lost)
- A daily cron job (Vercel cron or Cloud Scheduler) marks overdue loans and creates fine records
- Fine amount = `days_overdue × daily_rate`, capped at max fine

### Reservation Logic
1. **Book is available** (at least one copy with status='available'):
   - One copy is immediately set to status='reserved'
   - Reservation status = 'ready'
   - User has 48 hours to pick up (check out) before the reservation expires
2. **Book is unavailable** (all copies checked out):
   - Reservation status = 'pending'
   - Queue position assigned (max existing position + 1)
   - When any copy is returned:
     a. Check for pending reservations (ordered by queue_position)
     b. Set the copy status to 'reserved'
     c. Update reservation status to 'ready'
     d. Notify user (set notified_at)
     e. 48-hour pickup window starts
3. **Renewal blocking**:
   - Before renewing, check if any reservations with status='pending' exist for the book
   - If yes, block renewal and inform the user

### Checkout Flow
1. User clicks "Check Out" or "Reserve"
2. Verify user is authenticated and has no checkout block (total outstanding fines >= $10.00 blocks checkout)
3. Verify user hasn't exceeded max concurrent loans
4. If available → create loan, set copy status='checked_out', due_date = now + loan_period
5. If reservation exists and is 'ready' for this user → fulfill reservation, create loan
6. If unavailable → create reservation with queue_position

### Return Flow (Admin-Initiated or Auto via MCP)
1. Admin marks a book as returned
2. Set loan.returned_at = now, loan.status = 'returned'
3. Calculate any fines (if overdue) and create fine record
4. Set copy.status = 'available'
5. Trigger reservation check (see Reservation Logic step 2)

---

## API Endpoints

### Public (No Auth)
```
GET  /api/books                    # Search/browse books (query params: q, genre, author, item_type, page, limit)
GET  /api/books/:id                # Book detail with availability info
GET  /api/books/:id/reviews        # Public reviews for a book
```

### User (Clerk JWT Required)
```
POST /api/loans                    # Check out a book {book_id}
GET  /api/loans                    # My current loans
GET  /api/loans/history            # My loan history
POST /api/loans/:id/renew          # Renew a loan
POST /api/reservations             # Reserve a book {book_id}
GET  /api/reservations             # My reservations
DELETE /api/reservations/:id       # Cancel a reservation
GET  /api/fines                    # My fines
POST /api/reviews                  # Create/update review {book_id, rating, review_text}
GET  /api/reviews/mine             # My reviews
DELETE /api/reviews/:id            # Delete my review
POST /api/api-keys                 # Generate API key
GET  /api/api-keys                 # List my API keys
DELETE /api/api-keys/:id           # Revoke an API key
GET  /api/me                       # My profile
```

### Admin (Clerk JWT + role='admin')
```
POST /api/admin/books              # Create book
PUT  /api/admin/books/:id          # Update book
DELETE /api/admin/books/:id        # Delete book
POST /api/admin/books/:id/copies   # Add copies
GET  /api/admin/users              # List all users
GET  /api/admin/users/:id          # User detail with loans/fines
PUT  /api/admin/users/:id          # Edit user
DELETE /api/admin/users/:id        # Deactivate user
POST /api/admin/users/:id/promote  # Promote to admin
GET  /api/admin/loans              # All active loans
POST /api/admin/loans/:id/return   # Process return
GET  /api/admin/fines              # All fines
POST /api/admin/fines/:id/waive    # Waive a fine
GET  /api/admin/stats              # Dashboard stats
```

### MCP Endpoints (API Key Auth)
```
POST /mcp/user                     # User MCP server (SSE transport)
POST /mcp/admin                    # Admin MCP server (SSE transport)
```

---

## MCP Architecture

### Overview
Two MCP servers, both hosted on a single Google Cloud Run service with route-based separation. Both use **Streamable HTTP** transport (the modern MCP transport, replacing SSE).

### Authentication
- API key passed in the `Authorization: Bearer pt_usr_xxx` header
- Server validates key hash against `api_keys` table
- Key scope determines which tools are available
- Each request includes the user context (user_id resolved from the API key)

### User MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_books` | Search the catalogue | query, genre?, author?, item_type? |
| `get_book_details` | Get full book info + availability | book_id |
| `get_my_loans` | List user's current loans | — |
| `get_loan_history` | List past loans | limit?, offset? |
| `checkout_book` | Check out or reserve a book | book_id |
| `renew_loan` | Renew an active loan | loan_id |
| `get_my_reservations` | List active reservations | — |
| `cancel_reservation` | Cancel a reservation | reservation_id |
| `get_my_fines` | List fines and dues | — |
| `get_my_reviews` | Get user's ratings/reviews | — |
| `get_book_reviews` | Get public reviews for a book | book_id |
| `create_review` | Rate/review a book | book_id, rating, review_text? |

### Admin MCP Tools
All user tools plus:

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_book` | Add a book to the catalogue | title, author, isbn?, ... |
| `update_book` | Edit book metadata | book_id, fields... |
| `delete_book` | Remove a book | book_id |
| `lookup_user` | Find a user by email/name | query |
| `get_user_details` | Full user profile with loans/fines | user_id |
| `process_return` | Mark a book as returned | loan_id |
| `waive_fine` | Waive a fine | fine_id |
| `get_overdue_report` | List all overdue loans | — |
| `get_stats` | Library statistics | — |

### MCP Recommendation Strategy
The MCP does **not** include a built-in recommendation engine. Instead, it gives the AI agent all the data it needs to make recommendations:
- User's loan history (what they've read)
- User's reviews and ratings (what they liked/disliked)
- Book catalogue search (what's available)
- Book reviews from other users (social proof)

The AI agent (Claude, etc.) uses its own intelligence to synthesize this data and make personalized recommendations. This is intentional — the recommendation quality comes from the LLM, not from a collaborative filtering algorithm.

---

## Book Data Source

### Open Library API (Recommended)

**Why Open Library**:
- Completely free, no API key required
- 40+ million book records
- Rich metadata: title, author, ISBN, subjects, description, cover images, page count, publish date, publisher
- Cover images available at: `https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg`
- No rate limiting for reasonable use (we'll batch with delays)
- Public domain, open data

**Seeding Strategy**:
1. Curate a list of ISBNs across diverse genres (bestsellers, classics, sci-fi, mystery, romance, non-fiction, children's, etc.) — target ~1,000 books after filtering (some ISBNs won't have good Open Library data)
2. Fetch metadata from Open Library's Books API: `https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data`
3. Also use the Search API for genre-based discovery: `https://openlibrary.org/search.json?subject=science_fiction&limit=100`
4. Store in database with cover_image_url pointing to Open Library's cover service
5. Generate 1-3 `book_copies` per book (popular books get more copies)

**Genre Distribution** (target ~1,000 books):
| Genre | Count |
|-------|-------|
| Literary Fiction | 120 |
| Science Fiction | 100 |
| Fantasy | 100 |
| Mystery/Thriller | 100 |
| Romance | 80 |
| Non-Fiction | 120 |
| History | 60 |
| Science | 60 |
| Biography | 60 |
| Children's | 60 |
| Horror | 40 |
| Poetry | 30 |
| Graphic Novels | 30 |
| Self-Help | 40 |
| **Total** | **~1,000** |

**Fallback**: If Open Library is missing data for some ISBNs, supplement with Google Books API (free tier: 1,000 requests/day, no key required for basic search).

---

## Mock Data Strategy

### Users (50 mock users)
- Generated with Faker library
- 45 regular users, 5 admin users
- Realistic names, emails (using `@example.com` domain)
- Varied `max_loans` settings (3-10)
- Created over the past 2 years (varied `created_at`)

### Loans (500 mock loans)
- Distributed across 40 users (some users are heavy readers, some light)
- 80% returned, 15% active, 5% overdue
- Loan dates spanning the past 12 months
- Some loans renewed 1-2 times
- Return dates sometimes late (to generate fines)

### Reservations (30 mock reservations)
- 15 pending (waitlisted)
- 10 ready (waiting for pickup)
- 5 fulfilled

### Fines (40 mock fines)
- 60% pending, 25% paid, 15% waived
- Amounts ranging from $0.25 to $25.00
- Linked to overdue loans

### Reviews (200 mock reviews)
- Distributed across 30 users and 150 books
- Ratings follow a realistic bell curve (mean ~3.7)
- 60% include review text, 40% are rating-only
- Generated with varied lengths and tones

---

## Deployment & Infrastructure

### Vercel Configuration

**Frontend** (`frontend/vercel.json`):
```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist"
}
```

**Backend** (`api/vercel.json`):
```json
{
  "builds": [
    { "src": "app/main.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "app/main.py" }
  ]
}
```

### Google Cloud Run (MCP)
- Single container with both MCP servers
- Auto-scaling 0-10 instances
- 256MB memory, 1 vCPU
- Environment variables for database URL and Clerk keys
- Deployed via `gcloud run deploy`

### Environment Variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | Vercel + Cloud Run | Neon PostgreSQL connection string |
| `CLERK_SECRET_KEY` | Vercel | Backend JWT verification |
| `CLERK_PUBLISHABLE_KEY` | Frontend | Clerk React SDK |
| `CLERK_WEBHOOK_SECRET` | Vercel | User sync webhook verification |
| `VITE_API_URL` | Frontend | Backend API base URL |
| `MCP_SERVER_URL` | Reference | Cloud Run URL for MCP |

### Clerk Webhook
A webhook from Clerk → backend `/api/webhooks/clerk` syncs user creation/updates/deletions to our `users` table. This keeps our DB in sync without querying Clerk on every request.

---

## Prerequisites & What You Need to Set Up

Before the implementation agent starts, the following accounts/resources need to exist. **I need you to create these or give me credentials**:

### 1. Clerk Account
- **Action**: Create a Clerk app at [clerk.com](https://clerk.com)
- **Configure**: Enable Google and Email sign-in methods
- **Provide**: `CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`
- **Webhook**: Will be configured after backend is deployed (URL needed)

### 2. Neon Database
- **Action**: Create a Neon project at [neon.tech](https://neon.tech)
- **Provide**: `DATABASE_URL` (the connection string)
- **Note**: Free tier is sufficient (0.5 GB, 190 compute hours/mo)

### 3. Vercel Account
- **Action**: Ensure you have a Vercel account and the `vercel` CLI installed (`npm i -g vercel`)
- **Action**: Log in via `vercel login`
- **Provide**: The agent needs `vercel` CLI access to deploy

### 4. Google Cloud Account (for MCP)
- **Action**: Ensure you have a GCP project with Cloud Run enabled
- **Action**: Install `gcloud` CLI and authenticate (`gcloud auth login`)
- **Provide**: GCP project ID
- **Note**: Cloud Run free tier includes 2M requests/month

### Summary: What I Need From You
1. Create a Clerk app → give me the two API keys
2. Create a Neon database → give me the connection string
3. Confirm Vercel CLI is installed and logged in
4. Confirm gcloud CLI is installed, logged in, and give me the project ID

Everything else (database schema, migrations, seeding, deployment, MCP setup) will be handled by the implementation agent.

---

## Implementation Order

### Phase 1: Foundation
1. Initialize monorepo structure
2. Set up Neon database + Alembic migrations
3. Create all database tables
4. Set up FastAPI skeleton with Clerk auth middleware
5. Deploy backend to Vercel (verify it works)

### Phase 2: Core Backend
6. Implement book CRUD + search endpoints
7. Implement loan endpoints with business logic
8. Implement reservation system
9. Implement fine calculation
10. Implement review system
11. Implement API key management

### Phase 3: Data Seeding
12. Build book seeder (Open Library API)
13. Build mock user/loan/fine/review seeders
14. Run full seed

### Phase 4: Frontend
15. Set up React + Vite + Clerk
16. Build search/browse pages
17. Build book detail page
18. Build user dashboard (loans, history, fines)
19. Build review components
20. Build admin panel
21. Deploy frontend to Vercel

### Phase 5: MCP
22. Build user MCP server with all tools
23. Build admin MCP server
24. Deploy to Cloud Run
25. Test with Claude Desktop

### Phase 6: Polish
26. Responsive design pass
27. Error handling and loading states
28. End-to-end testing
29. Final deployment and verification

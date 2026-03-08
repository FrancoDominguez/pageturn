# PageTurn — Product Requirements Document

---

## 1. Product Overview

PageTurn is a full-stack library catalogue and management system with:
- Public book search and browsing
- Member loan management (checkout, renew, reserve, return)
- Fine calculation and management
- Book reviews and ratings
- Admin dashboard for library operations
- AI assistant integration via MCP (Model Context Protocol)

---

## 2. User Roles

### 2.1 Visitor (Unauthenticated)
No account required. Can browse and search only.

### 2.2 Member (Authenticated, role='user')
Authenticated via Clerk SSO. Can manage personal loans, reviews, and reservations.

### 2.3 Administrator (Authenticated, role='admin')
Same auth as member but with `role='admin'` in database and Clerk metadata. Full CRUD access to all resources.

---

## 3. Feature Specifications

### F1: Book Search & Browse

**Priority**: P0 (Core)

**Description**: Full-text search across the book catalogue with filtering and sorting.

**Acceptance Criteria**:
- [ ] Search bar on homepage accepts free-text queries
- [ ] Results match against title (highest weight), author, description, genre
- [ ] Results return within 200ms for any query
- [ ] Each result card shows: cover image, title, author, average rating, genre tag, availability status
- [ ] Filter by: genre (multi-select), item type (book/audiobook/dvd/ebook/magazine), availability (available only)
- [ ] Sort by: relevance (default), title A-Z, title Z-A, rating high-low, publication year
- [ ] Pagination: 20 results per page, page navigation at bottom
- [ ] Empty state: "No books found" with suggestion to adjust filters
- [ ] No authentication required

**Search Implementation**:
- PostgreSQL full-text search with GIN index on `tsvector` column
- Weighted search: title (A), author (B), description (C), genre (D)
- `ts_rank` for relevance scoring
- Additional filters applied as WHERE clauses alongside FTS

---

### F2: Book Detail Page

**Priority**: P0 (Core)

**Description**: Detailed view of a single book with all metadata, availability, and reviews.

**Acceptance Criteria**:
- [ ] Displays: cover image (large), title, author, ISBN, publication year, page count, publisher, language, description, genres, item type
- [ ] Average rating displayed as stars (1-5) with count "(847 ratings)"
- [ ] Availability section shows:
  - If available: green badge "Available — N copies", "Check Out" button
  - If all copies out: orange badge "All copies checked out — Returns [earliest due date]", "Reserve" button with queue position info
  - If user has it checked out: blue badge "You have this book — Due [date]", "Renew" button (if eligible)
- [ ] Author name is a clickable link → navigates to `/?author=AuthorName` showing all books by that author
- [ ] Reviews section below metadata (see F7)
- [ ] Below the Reviews section, a "More by [Author Name]" horizontal scroll row shows other books by the same author (reuses homepage ScrollCard component). Data: `GET /api/books?author=AuthorName&limit=10`. Hidden if author has only 1 book in catalogue.
- [ ] Breadcrumb navigation (contextual):
  - From search: `Home > Search Results > [Title]`
  - From genre accordion: `Home > [Genre] > [Title]` (genre links to `/?genre=X`)
  - Direct nav: `Home > [Title]`
  - Implementation: `from` query param or referrer-based
- [ ] No authentication required for viewing; buttons redirect to sign-in if not logged in

---

### F3: User Authentication

**Priority**: P0 (Core)

**Description**: SSO authentication via Clerk with Google and email providers.

**Acceptance Criteria**:
- [ ] "Sign In" button in nav bar opens Clerk sign-in modal
- [ ] Supports: Google SSO, Email + password, Email magic link
- [ ] After sign-in, user is synced to our database via Clerk webhook
- [ ] Nav bar updates to show user avatar, name, and "My Account" dropdown
- [ ] Dropdown contains: My Loans, Loan History, Fines & Dues, My Reviews, AI Assistant, Sign Out
- [ ] Admin users see additional "Admin" link in dropdown
- [ ] Session persists across page reloads (Clerk handles this)
- [ ] Sign out clears session and redirects to homepage

**Clerk Webhook Sync**:
- Webhook endpoint: `POST /api/webhooks/clerk`
- Events: `user.created`, `user.updated`, `user.deleted`
- On `user.created`: insert into `users` table with `clerk_id`, `email`, `first_name`, `last_name`, `role='user'`
- On `user.updated`: update matching row
- On `user.deleted`: set `deleted_at` timestamp on the user record. Preserve all loan, fine, and review records. Remove user from active views (e.g., admin user list filters by `deleted_at IS NULL`). Do NOT cascade-delete related records.

---

### F4: Book Checkout

**Priority**: P0 (Core)

**Description**: Members can check out available books.

**Acceptance Criteria**:
- [ ] "Check Out" button visible on book detail page when book is available
- [ ] Clicking triggers checkout flow:
  1. Verify user is authenticated → redirect to sign-in if not
  2. Verify user has no checkout block (checkout blocked when total outstanding fines >= $10.00)
  3. Verify user hasn't exceeded max concurrent loans (default 5)
  4. Find an available copy (status='available')
  5. Create loan record: `checked_out_at=now`, `due_date=now + loan_period`, `status='active'`
  6. Update copy status to 'checked_out'
  7. Inline green banner replaces action buttons — "Checked out! Due back [date]" + "View My Loans →" link + toast notification
- [ ] If no copies available: auto-create a reservation (pending waitlist) and return `{reservation, queue_position}` instead of `{loan, due_date}`. Single endpoint handles both outcomes. Inline blue banner — "You're #N in the waitlist. We'll hold it 48h when available." + "View My Reservations →" link + toast
- [ ] If checkout blocked by fines: coral banner + disabled button — "Checkout paused — $X.XX in outstanding fines. [View Fines →]"
- [ ] If max loans reached: coral banner + disabled button — "Limit reached (N books). Return a book to check out more. [View My Loans →]"
- [ ] If fulfilling a reservation: reservation status → 'fulfilled', copy already reserved
- [ ] The system automatically selects an available copy. Users do not choose which physical copy they receive.
- [ ] Loan periods by item type:
  - Book/Ebook: 14 days
  - DVD/Magazine: 7 days
  - Audiobook: 21 days

---

### F5: Loan Management

**Priority**: P0 (Core)

**Description**: Members view and manage their current loans and history.

**My Loans Page** (`/loans`):
- [ ] Table/card list of all active loans
- [ ] Each loan shows: book cover thumbnail, title, author, checked out date, due date, days remaining (or days overdue in red)
- [ ] "Renew" button per loan (see renewal rules below)
- [ ] "Return" info text: "Return this book at the library desk" (returns are admin-processed)
- [ ] Visual indicator for overdue loans (red highlight)
- [ ] Empty state: "No active loans. Browse the catalogue to find your next read!"

**Loan History Page** (`/history`):
- [ ] Chronological list of all past loans (returned)
- [ ] Each entry: book cover, title, author, checkout date, return date, "Leave Review" link if no review exists
- [ ] Each history entry includes an Action column: "Borrow Again" link (→ book detail) if book exists, or muted "Unavailable" if deleted
- [ ] Duration column removed; replaced by Action column
- [ ] Pagination: 20 per page
- [ ] Logged-in homepage shows "Currently Reading" section above Staff Picks with active loans as scroll cards with due date badges
- [ ] No active loans: "Welcome back, [Name]! Browse to find your next read."
- [ ] CTA Banner hidden for logged-in users (wrapped in `<SignedOut>`)
- [ ] When user has a recently returned book (last 7 days) with no review, show a dismissible card above the loans table and history table: "How was **[Book Title]**? Your rating helps other readers. [Rate it →]" (links to book detail page reviews section)
- [ ] Nudge is dismissible (X button, stored in localStorage per book_id so it doesn't reappear)
- [ ] Only show nudge for the most recent unreviewed return (not all of them)

**Renewal Rules**:
- [ ] Max 2 renewals per loan
- [ ] Renewal extends due date by the original loan period from the current date
- [ ] Renewal blocked if any pending reservation exists for the same book
- [ ] Renewal blocked if loan is overdue by more than 7 days
- [ ] On renewal: update `due_date`, increment `renewed_count`
- [ ] If blocked: show reason ("Cannot renew — someone is waiting for this book" or "Max renewals reached")

---

### F6: Reservation System

**Priority**: P0 (Core)

**Description**: Members can reserve books that are currently unavailable.

**Acceptance Criteria**:

**Reserve an available book** (immediate):
- [ ] If at least one copy has status='available':
  1. Set one copy to status='reserved'
  2. Create reservation: `status='ready'`, `expires_at=now+48h`
  3. Show: "Reserved! Pick up within 48 hours."
  4. User must check out within 48h or reservation expires

**Reserve an unavailable book** (waitlist):
- [ ] If all copies are checked out:
  1. Create reservation: `status='pending'`, `queue_position=max+1`
  2. Show: "You're #N in the waitlist. We'll notify you when it's available."

**When a book is returned**:
- [ ] Check for pending reservations ordered by `queue_position`
- [ ] If found: set copy status='reserved', reservation status='ready', set `notified_at=now`, `expires_at=now+48h`
- [ ] If not found: set copy status='available'

**Reservation expiry**:
- [ ] A cron job checks every hour for expired reservations (where `expires_at < now` and status='ready')
- [ ] Expired: set reservation status='expired', copy status='available', trigger next-in-queue check

**Queue reordering on cancel**:
- [ ] When a user cancels a reservation, all reservations for the same book with a higher `queue_position` are decremented by 1. This is handled atomically in the service layer within a single transaction.

**My Reservations** (on loans page or separate section):
- [ ] List of active reservations with status, queue position, book info
- [ ] "Cancel" button to cancel a reservation
- [ ] Ready reservation triggers prominent alert banner at TOP of LoansPage: "Your reservation for [Title] is ready! Pick up by [date] (Xh remaining)" + "Check Out Now →" link
- [ ] Coral notification dot (8px) appears on "My Loans" nav link when any reservation is ready

**Renewal blocking**:
- [ ] When a user tries to renew, check if any reservations with status='pending' exist for that book (not book_copy — any copy of the same book)
- [ ] If yes: block renewal, message "Cannot renew — another member is waiting for this book"

---

### F7: Reviews & Ratings

**Priority**: P1 (Important)

**Description**: Members can rate and review books they've borrowed.

**Acceptance Criteria**:
- [ ] On book detail page: "Reviews" section shows all reviews for that book
- [ ] Each review shows: avatar (initials), display name, star rating (1-5), date, review text
- [ ] Reviews sorted by most recent first
- [ ] Average rating computed and displayed on book card and detail page
- [ ] "Write a Review" button visible to authenticated users who have borrowed this book (active or returned loan exists)
- [ ] Review form: star rating selector (required), text area for review (optional), Submit button
- [ ] One review per user per book (UNIQUE constraint)
- [ ] Users can edit or delete their own review
- [ ] On review submit/update/delete: recalculate `avg_rating` and `rating_count` on the book record (denormalized)
- [ ] **My Reviews** page (`/reviews`): list of all reviews the user has written with links to books
- [ ] When user has a recently returned book (last 7 days) with no review, show a dismissible card above the loans table and history table: "How was **[Book Title]**? Your rating helps other readers. [Rate it →]" (links to book detail page reviews section)
- [ ] Nudge is dismissible (X button, stored in localStorage per book_id so it doesn't reappear)
- [ ] Only show nudge for the most recent unreviewed return (not all of them)

---

### F8: Fines & Dues

**Priority**: P1 (Important)

**Description**: Transparent fine tracking and management.

**User Fines Page** (`/fines`):
- [ ] List of all fines with: book title, reason, amount, status (pending/paid/waived), date
- [ ] Total outstanding balance prominently displayed
- [ ] If balance >= $10.00: warning banner "Your account has a checkout hold. Please resolve outstanding fines."
- [ ] Fine detail: breakdown showing daily rate, days overdue, total

**Fine Calculation Logic**:
- [ ] Fines accrue starting the day after the due date
- [ ] Daily rates by item type:
  - Book/Ebook: $0.25/day
  - DVD: $1.00/day
  - Audiobook: $0.50/day
  - Magazine: $0.10/day
- [ ] Maximum fine per item: $25.00
- [ ] Fine created when: book is returned late OR a daily cron job detects overdue active loans
- [ ] For active overdue loans: fine amount recalculated daily (not stored as a record until returned)
- [ ] Display: show calculated fine amount for active overdue loans even before a fine record exists
- [ ] Lost item fee: $30 default or replacement cost if stored in book metadata

**Lost Item Processing**:
- [ ] Admin marks a loan as lost via `POST /api/admin/loans/:id/lost`
- [ ] Creates a fine record with reason='lost_item' for $30 default or the book's `replacement_cost` if stored in book metadata
- [ ] Sets the book copy `status='lost'`
- [ ] Sets the loan `status='returned'` with `returned_at=now()`
- [ ] The copy is removed from availability counts (lost copies are not available for checkout)

**Admin Fine Management**:
- [ ] View all fines across all users
- [ ] Filter by status: pending, paid, waived
- [ ] "Waive" button: sets `status='waived'`, records `waived_by` (admin user_id) and `waived_at`
- [ ] Waiving a fine reduces the user's outstanding balance

---

### F9: Admin Book Management

**Priority**: P1 (Important)

**Description**: CRUD operations for books in the catalogue.

**Admin Books Page** (`/admin/books`):
- [ ] Searchable table of all books with columns: cover, title, author, genre, copies, status
- [ ] "Add Book" button opens a form/modal with fields:
  - Title (required), Author (required), ISBN, ISBN-13
  - Description (textarea), Genre (dropdown + multi-select for secondary genres)
  - Item type (dropdown: book/audiobook/dvd/ebook/magazine)
  - Cover image URL, Page count, Publication year, Publisher, Language
- [ ] "Edit" button per row opens same form pre-filled
- [ ] "Delete" button with confirmation dialog
- [ ] "Add Copies" button per book: specify quantity and condition
- [ ] Admin can view all copies of a book with barcode, condition, and status. Clicking the copy count on a book row opens a CopyManagementModal.
- [ ] Admin can update individual copy condition or mark a copy as damaged/lost
- [ ] Validation: title and author required, ISBN format check if provided

---

### F10: Admin User Management

**Priority**: P1 (Important)

**Description**: Admins can view and manage all user accounts.

**Admin Users Page** (`/admin/users`):
- [ ] Searchable table: name, email, role, active loans, total fines, joined date
- [ ] Click user → detail view showing:
  - Profile info (name, email, role, max_loans setting)
  - Current loans with due dates
  - Loan history
  - Active reservations
  - Fines (with waive buttons)
  - Reviews
- [ ] "Edit User" button: modify max_loans, role
- [ ] "Promote to Admin" / "Demote to User" with confirmation
- [ ] Role changes sync to Clerk `publicMetadata.role`

---

### F11: Admin Dashboard

**Priority**: P2 (Nice to Have)

**Description**: Overview statistics for administrators.

**Admin Home** (`/admin`):
- [ ] Stat cards: Total books, Total copies, Active loans, Overdue loans, Total users, Open fines total
- [ ] Recent activity feed: latest checkouts, returns, new users
- [ ] Quick action buttons: Add Book, View Overdue, Manage Fines

---

### F12: AI Assistant

**Priority**: P1 (Important)

**Description**: Users set up and manage their AI assistant connection via MCP.

**AI Assistant Page** (accessible from user dropdown):
- [ ] Setup Guide section with numbered steps (generate key, open Claude Desktop, paste config, restart)
- [ ] "Copy Config" button generates full `claude_desktop_config.json` with MCP URL pre-filled
- [ ] Platform-specific config file paths (macOS, Windows, Linux)
- [ ] "Try These Prompts" section with 3 example queries
- [ ] List of user's API keys: name, key prefix (e.g., "pt_usr_3f..."), created date, last used, status
- [ ] "Generate New Key" button:
  1. Name input (e.g., "Claude Desktop")
  2. Key generated: `pt_usr_<32 random hex chars>` (user) or `pt_adm_<32 random hex chars>` (admin)
  3. **Show key once** in a copy-to-clipboard modal with warning: "Save this key — you won't see it again"
  4. Store SHA-256 hash of key + prefix for identification
- [ ] "Revoke" button per key (sets `revoked_at`, key stops working immediately)
- [ ] Admin keys only available to admin users

---

### F13: MCP — User AI Assistant

**Priority**: P1 (Important)

**Description**: MCP server exposing user-level library tools for AI agents.

**Tools**:

| Tool | Params | Returns | Description |
|------|--------|---------|-------------|
| `search_books` | `query: str, genre?: str, author?: str, item_type?: str, limit?: int` | `{books: [{id, title, author, genre, rating, available, cover_url}]}` | Search the catalogue |
| `get_book_details` | `book_id: str` | `{id, title, author, isbn, description, genres, rating, rating_count, available_copies, total_copies, due_date_if_checked_out, cover_url, page_count, pub_year}` | Full book info |
| `get_my_loans` | — | `{loans: [{id, book_title, book_author, checked_out_at, due_date, days_remaining, can_renew, cover_url}]}` | Current loans |
| `get_loan_history` | `limit?: int, offset?: int` | `{loans: [{id, book_title, checked_out_at, returned_at, rating_given}]}` | Past loans |
| `checkout_book` | `book_id: str` | `{success: bool, loan_id?, due_date?, error?, waitlist_position?}` | Check out or reserve |
| `renew_loan` | `loan_id: str` | `{success: bool, new_due_date?, error?}` | Renew a loan |
| `get_my_reservations` | — | `{reservations: [{id, book_title, status, queue_position, expires_at}]}` | Active reservations |
| `cancel_reservation` | `reservation_id: str` | `{success: bool}` | Cancel a reservation |
| `get_my_fines` | — | `{fines: [{id, book_title, amount, reason, status, created_at}], total_outstanding: float}` | Fines and dues |
| `get_my_reviews` | — | `{reviews: [{id, book_title, rating, review_text, created_at}]}` | User's reviews |
| `get_book_reviews` | `book_id: str` | `{reviews: [{user_name, rating, review_text, created_at}], avg_rating: float}` | Book's reviews |
| `create_review` | `book_id: str, rating: int, review_text?: str` | `{success: bool, review_id?}` | Rate/review a book |
| `get_reading_profile` | — | `{total_books_read, favorite_genres, favorite_authors, avg_rating_given, recent_reads, highly_rated}` | Aggregated reading profile for recommendations |

---

### F14: MCP — Admin AI Assistant

**Priority**: P1 (Important)

**Description**: MCP server with all user tools plus admin operations.

**Additional Admin Tools**:

| Tool | Params | Returns | Description |
|------|--------|---------|-------------|
| `create_book` | `title: str, author: str, isbn?: str, description?: str, genre?: str, genres?: list, item_type?: str, cover_image_url?: str, page_count?: int, pub_year?: int, publisher?: str, copies?: int` | `{success: bool, book_id?}` | Add book |
| `update_book` | `book_id: str, [any book field]` | `{success: bool}` | Edit book |
| `delete_book` | `book_id: str` | `{success: bool}` | Remove book |
| `lookup_user` | `query: str` | `{users: [{id, name, email, role, active_loans, total_fines}]}` | Find user |
| `get_user_details` | `user_id: str` | `{full user profile with loans, fines, reviews}` | User detail |
| `process_return` | `loan_id: str` | `{success: bool, fine_amount?, fine_reason?}` | Mark returned |
| `waive_fine` | `fine_id: str` | `{success: bool}` | Waive a fine |
| `get_overdue_report` | — | `{overdue_loans: [{user_name, book_title, due_date, days_overdue, fine_amount}]}` | Overdue list |
| `get_stats` | — | `{total_books, total_copies, active_loans, overdue_loans, total_users, open_fines_amount}` | Library stats |

---

### F15: Staff Picks
**Priority**: Medium
**Description**: Admins can mark books as "Staff Picks" with a personal note. Staff picks are prominently featured on the homepage in a dedicated section and as a rotating featured book hero. This gives the library a curated, personal feel.

**Acceptance Criteria**:
- [ ] Books can be marked/unmarked as staff picks by admins
- [ ] Each staff pick has an optional note (1-2 sentences from the "librarian")
- [ ] Homepage displays a featured staff pick in the hero section (rotates on page load)
- [ ] A "Staff Picks" section shows all staff-picked books
- [ ] Staff picks are filterable via the API (`GET /api/books?staff_picks=true`)
- [ ] Admin panel has a toggle to set/unset staff pick status with note field

---

### F16: Top Picks / Highest Rated
**Priority**: Low
**Description**: A "Top Rated" section on the homepage displays books sorted by average rating. This is a derived view (no new DB fields needed) that makes the catalogue feel dynamic.

**Acceptance Criteria**:
- [ ] Homepage displays a "Top Rated" section with highest-rated books
- [ ] Books are sorted by avg_rating DESC, with a minimum of 3 ratings to qualify
- [ ] API supports sorting by rating (`GET /api/books?sort=rating`)

---

## 4. Scheduled Jobs (Cron)

PageTurn uses Vercel Cron to run two recurring background jobs:

| Job | Schedule | Description |
|-----|----------|-------------|
| Overdue detection | Daily at 2:00 AM UTC | Marks active loans past their `due_date` as `status='overdue'`. For loans already overdue, recalculates accrued fine amounts. |
| Reservation expiry | Hourly | Finds reservations where `status='ready'` and `expires_at < now()`. Sets them to `status='expired'`, returns copy to `status='available'`, and triggers the next-in-queue check. |

**Implementation**: Vercel Cron endpoints (`/api/cron/overdue`, `/api/cron/expire-reservations`) secured with `CRON_SECRET` header verification. Configured in `vercel.json`.

---

## 5. Non-Functional Requirements

### Performance
- Search results in < 200ms
- Page load in < 2 seconds
- API response in < 500ms for any endpoint

### Security
- All API endpoints validate Clerk JWT (except public search/browse)
- Admin endpoints verify `role='admin'`
- API keys hashed with SHA-256, never stored in plaintext
- Clerk webhook signatures verified
- CORS restricted to frontend domain
- SQL injection prevented by SQLAlchemy parameterized queries
- Rate limiting on auth endpoints (Clerk handles this)

### Scalability
- Vercel serverless auto-scales
- Neon serverless Postgres auto-scales
- Cloud Run auto-scales 0-10 instances
- Designed for ~1,000 books but architecture supports 100,000+

### Accessibility
- Semantic HTML
- ARIA labels on interactive elements
- Keyboard navigable
- Color contrast meets WCAG AA
- Screen reader friendly

---

## 6. Mock Data

### Mock Data Completeness
The seed data must make the platform feel **alive and in motion** for demo purposes. Every feature area must have populated data:

- **Active loans**: 75 currently checked out books across 30+ users
- **Overdue loans**: 25 books past due date (generates visible fines)
- **Recent returns**: 50+ books returned in the last 7 days (shows "Recently Returned" activity)
- **Pending fines**: 24 unpaid fines visible in user accounts
- **Active reservations**: 15 books with waitlists (queue positions 1-3)
- **Reviews with text**: 120+ reviews with written text (not just ratings)
- **Staff picks**: 15-20 curated books with librarian notes
- **Varied availability**: Mix of available, checked out, and reserved copies across all genres
- **User activity history**: Each mock user should have 5-15 historical loans to show reading history

The goal is zero empty states in the demo — every page, sidebar widget, and section should have data to display.

---

## 7. Out of Scope (v1)

- Payment processing (fines are tracked but not collected online)
- Email notifications (reservation ready, overdue reminders)
- Book recommendation algorithm (delegated to AI agent)
- Multi-branch library support
- Barcode scanning
- Physical card printing
- Mobile native app

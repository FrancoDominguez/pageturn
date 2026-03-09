# PageTurn — Frontend Specification

**Framework**: React 18 + TypeScript
**Build**: Vite 5
**Styling**: TailwindCSS 3
**Auth**: Clerk React SDK (`@clerk/clerk-react`)
**Routing**: React Router v6
**State**: React Query (TanStack Query) for server state
**Hosting**: Vercel

---

## Design System — "Bold Modern" (Finalized)

### Design Tokens (CSS Custom Properties in `index.css`)

```css
:root {
  --color-primary: #ff6b6b;
  --color-primary-hover: #ff5252;
  --color-secondary: #4cc9f0;
  --color-background: #fafafa;
  --color-surface: #ffffff;
  --color-text-primary: #0d1117;
  --color-text-secondary: #555555;
  --color-text-muted: #999999;
  --color-border: #e5e5e5;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ff6b6b;
  --font-heading: 'Space Grotesk', sans-serif;
  --font-body: 'DM Sans', sans-serif;
  --radius-card: 14px;
  --radius-button: 50px;
  --radius-pill: 50px;
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-hover: 0 12px 40px rgba(0, 0, 0, 0.1);
  --shadow-modal: 0 24px 64px rgba(0, 0, 0, 0.18);
}
```

### Tailwind Config

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        'primary-hover': 'var(--color-primary-hover)',
        secondary: 'var(--color-secondary)',
        background: 'var(--color-background)',
        surface: 'var(--color-surface)',
        'text-primary': 'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-muted': 'var(--color-text-muted)',
        border: 'var(--color-border)',
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        error: 'var(--color-error)',
      },
      fontFamily: {
        heading: ['Space Grotesk', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      borderRadius: {
        card: '14px',
        button: '50px',
        pill: '50px',
      },
    },
  },
};
```

### Key Visual Patterns

- **Gradient**: `linear-gradient(135deg, #ff6b6b, #4cc9f0)` — used on CTA buttons, logo accent, avatar circles
- **Card hover**: `translateY(-4px)`, `box-shadow: 0 12px 40px rgba(0,0,0,.1)`, coral border
- **Nav bar**: Dark (`#0d1117`), sticky, 72px tall, integrated search bar with coral Search button
- **Sub-nav**: White background, bottom border, tab-style links with coral underline on active
- **Data tables**: White card with 16px border-radius, `#fafafa` header row, uppercase 12px column headers, subtle row borders
- **Status pills**: Rounded 50px, colored background tint + bold text (green=active, yellow=due-soon, red=overdue)

### Fonts (Google Fonts CDN)

```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

---

## Routing Table

| Path | Component | Auth | Description |
|------|-----------|------|-------------|
| `/` | `HomePage` | No | Browse (accordion) + search results (grid) |
| `/books/:id` | `BookDetailPage` | No | Book detail + reviews |
| `/loans` | `LoansPage` | User | Active loans + reservations |
| `/history` | `HistoryPage` | User | Loan history |
| `/fines` | `FinesPage` | User | Fines & dues |
| `/reviews` | `MyReviewsPage` | User | User's reviews |
| `/ai-assistant` | `AIAssistantPage` | User | AI assistant setup & API keys |
| `/admin` | `AdminDashboard` | Admin | Stats overview |
| `/admin/books` | `AdminBooksPage` | Admin | Book CRUD |
| `/admin/users` | `AdminUsersPage` | Admin | User management |
| `/admin/users/:id` | `AdminUserDetail` | Admin | User detail |
| `/admin/fines` | `AdminFinesPage` | Admin | Fine management |
| `/sign-in/*` | Clerk `<SignIn />` | No | Clerk sign-in page |
| `/sign-up/*` | Clerk `<SignUp />` | No | Clerk sign-up page |

---

## Component Tree

```
App
├── ClerkProvider
│   └── QueryClientProvider
│       └── BrowserRouter
│           ├── Layout
│           │   ├── Navbar
│           │   │   ├── Logo (links to /)
│           │   │   ├── NavLinks (Browse | My Loans)
│           │   │   └── AuthSection
│           │   │       ├── <SignedOut> → SignInButton
│           │   │       └── <SignedIn> → UserMenu (avatar + dropdown, "Fines & Dues" shows outstanding balance badge if > $0)
│           │   ├── <Outlet /> (page content)
│           │   └── Footer (dark #0d1117 bg, logo, tagline, nav links: Browse/My Loans/Privacy/Terms, copyright)
│           │
│           ├── Route "/" → HomePage
│           │   ├── [Browse Mode — default]
│           │   │   ├── <SignedIn> CurrentlyReadingSection (active loans as scroll cards with due date badges)
│           │   │   ├── FeaturedHero (Staff Pick of the Week)
│           │   │   │   ├── FeaturedBookInfo (title, author, desc, rating)
│           │   │   │   ├── CoverImage (tilted, gradient glow)
│           │   │   │   └── CheckOutButton
│           │   │   └── AccordionGenreSections
│           │   │       └── GenreAccordion (×N: Staff Picks, Top Rated, Fiction, Sci-Fi, etc.)
│           │   │           ├── AccordionHeader (title, count badge, chevron)
│           │   │           └── HorizontalScrollRow
│           │   │               └── ScrollCard (×N)
│           │   │                   ├── CoverImage
│           │   │                   ├── BookInfo (title, author, rating)
│           │   │                   ├── ItemTypeBadge (if not 'book')
│           │   │                   └── AvailabilityBadge
│           │   ├── [Search Mode — activated by nav search]
│           │   │   ├── SearchResultsHeader (query, count, sort dropdown)
│           │   │   ├── FilterBar (genre chips, item type, availability toggle)
│           │   │   ├── BookGrid
│           │   │   │   └── BookCard (×N)
│           │   │   │       ├── CoverImage
│           │   │   │       ├── BookInfo (title, author, rating)
│           │   │   │       ├── ItemTypeBadge (if not 'book')
│           │   │   │       ├── GenreTag
│           │   │   │       └── AvailabilityBadge
│           │   │   └── Pagination
│           │   └── <SignedOut> CTABanner + Footer
│           │
│           ├── Route "/books/:id" → BookDetailPage
│           │   ├── Breadcrumb (contextual: from search / genre / direct)
│           │   ├── BookDetailLayout (2-column)
│           │   │   ├── CoverImage (large)
│           │   │   └── BookMetadata
│           │   │       ├── Title, Author
│           │   │       ├── StarRating
│           │   │       ├── AvailabilityInfo
│           │   │       ├── GenreTags
│           │   │       ├── MetaLine (year, pages, ISBN)
│           │   │       ├── Description
│           │   │       └── ActionButtons
│           │   │           ├── CheckoutButton
│           │   │           └── ReserveButton
│           │   ├── ReviewsSection
│           │   │   ├── ReviewSummary (avg, distribution)
│           │   │   ├── ReviewForm (if eligible)
│           │   │   └── ReviewList
│           │   │       └── ReviewCard (×N)
│           │   └── MoreByAuthor (horizontal scroll row, hidden if 1 book)
│           │
│           ├── Route "/loans" → LoansPage (ProtectedRoute)
│           │   ├── SubNav (Loans | History | Fines (badge with $amount if > 0) | Reviews | AI Assistant)
│           │   ├── PageHeader "My Loans"
│           │   ├── ReviewNudge (dismissible, most recent unreviewed return)
│           │   ├── ReadyReservationAlert (green banner per ready reservation)
│           │   ├── OverdueAlert (coral banner if overdue books)
│           │   ├── LoansTable
│           │   │   ├── TableHeader (dark row)
│           │   │   └── LoanRow (×N)
│           │   │       ├── BookCell (thumbnail + title + author)
│           │   │       ├── ItemType (if not 'book')
│           │   │       ├── DateCells (checked out, due date)
│           │   │       ├── StatusPill (active/due-soon/overdue)
│           │   │       ├── RenewalsCount
│           │   │       └── ActionCell (RenewLink or disabled note)
│           │   ├── ReturnInfoBanner ("Return books at the library front desk")
│           │   └── ReservationsSection
│           │       ├── SectionHeader "My Reservations"
│           │       └── ReservationCard (×N)
│           │           ├── BookCell (thumbnail + title + author)
│           │           ├── StatusPill (pending/ready)
│           │           ├── QueuePosition (if pending)
│           │           ├── ExpiresAt (if ready)
│           │           └── CancelLink
│           │
│           ├── Route "/history" → HistoryPage (ProtectedRoute)
│           │   ├── SubNav (Loans | History | Fines (badge with $amount if > 0) | Reviews | AI Assistant)
│           │   ├── PageHeader "Loan History"
│           │   ├── ReviewNudge (dismissible, most recent unreviewed return)
│           │   ├── HistoryTable
│           │   │   ├── MonthGroupRow (×N, spanning full width)
│           │   │   └── HistoryRow (×N)
│           │   │       ├── BookCell (thumbnail + title + author)
│           │   │       ├── DateCells (borrowed, returned)
│           │   │       ├── ActionCell (BorrowAgain link or muted "Unavailable")
│           │   │       ├── ReviewCell (stars or WriteReviewLink)
│           │   │       └── FineCell (amount or dash)
│           │   └── Pagination
│           │
│           ├── Route "/fines" → FinesPage (ProtectedRoute)
│           │   ├── SubNav (Loans | History | Fines (badge with $amount if > 0) | Reviews | AI Assistant)
│           │   ├── OutstandingBalance (single prominent display, not stat cards)
│           │   ├── WarningBanner (if balance >= $10.00)
│           │   └── FinesTable
│           │       └── FineRow (×N)
│           │           ├── BookInfo (title + author)
│           │           ├── ReasonPill
│           │           ├── AmountCell (colored by status)
│           │           ├── StatusPill (pending/paid/waived)
│           │           └── DateCell
│           │
│           ├── Route "/reviews" → MyReviewsPage (ProtectedRoute)
│           │   ├── SubNav (Loans | History | Fines (badge with $amount if > 0) | Reviews | AI Assistant)
│           │   ├── PageHeader "My Reviews"
│           │   └── ReviewsList
│           │       └── ReviewCard (×N)
│           │           ├── BookCell (thumbnail + title + author)
│           │           ├── StarRating
│           │           ├── ReviewText
│           │           ├── DateCell
│           │           └── EditDeleteActions
│           │
│           ├── Route "/ai-assistant" → AIAssistantPage (ProtectedRoute)
│           │   ├── SubNav (Loans | History | Fines (badge with $amount if > 0) | Reviews | AI Assistant)
│           │   ├── SetupGuide (numbered steps + config code block + Copy Config button)
│           │   ├── ApiKeyManager
│           │   │   ├── ApiKeyList
│           │   │   ├── GenerateKeyButton
│           │   │   └── KeyRevealModal
│           │   └── ExamplePrompts (3 prompt cards)
│           │
│           └── Route "/admin/*" → AdminLayout (ProtectedRoute + AdminOnly)
│               ├── AdminSidebar
│               │   ├── Link: Dashboard
│               │   ├── Link: Books
│               │   ├── Link: Users
│               │   └── Link: Fines
│               ├── Route "/admin" → AdminDashboard
│               │   └── StatCards (4-6)
│               ├── Route "/admin/books" → AdminBooksPage
│               │   ├── SearchInput
│               │   ├── AddBookButton → BookFormModal
│               │   └── BooksTable
│               │       └── BookRow (×N) → EditBookModal
│               ├── Route "/admin/users" → AdminUsersPage
│               │   ├── SearchInput
│               │   └── UsersTable
│               │       └── UserRow (×N) → link to detail
│               ├── Route "/admin/users/:id" → AdminUserDetail
│               │   ├── UserProfile
│               │   ├── UserLoans
│               │   ├── UserFines (with waive buttons)
│               │   └── UserReviews
│               └── Route "/admin/fines" → AdminFinesPage
│                   ├── FilterTabs (All | Pending | Paid | Waived)
│                   └── FinesTable
│                       └── FineRow (×N) with WaiveButton
```

---

## Page Specifications

### HomePage (`/`)

**Layout**: Two modes — **Browse** (default) and **Search Results** (activated by nav search bar).

**Mockup**: `mockups/option-c4-home.html`

#### Browse Mode (Default)

The landing experience is a curated discovery layout:

0. **Currently Reading** (logged-in only, `<SignedIn>` wrapper): Horizontal scroll section with active loan cards showing due date badges (green when >3 days remaining, yellow when 0-3 days, red when overdue). No active loans: "Welcome back, [Name]! Browse to find your next read." Data: `useQuery(['my-loans'], fetchMyLoans, { enabled: isSignedIn })`
1. **Featured Hero** — "Staff Pick of the Week" dark band with tilted cover, gradient glow, book info, and "Check Out" CTA
2. **Accordion Genre Sections** — Collapsible genre rows (Staff Picks, Top Rated, Fiction, Sci-Fi & Fantasy, Mystery & Thriller, Non-Fiction, New Arrivals) with horizontal-scrolling book cards. **Note**: Genre sections are hardcoded frontend constants (not dynamic from API). Each section fetches books via `GET /api/books?genre=X&sort=rating&limit=20`. The "Staff Picks" section uses `?staff_picks=true` and "Top Rated" uses `?sort=rating`.
3. **CTA Banner** — "Create Your Free Account" prompt for visitors (wrapped in `<SignedOut>`, hidden for logged-in users)
4. **Footer**

**Data Fetching (Browse)**:
- `useQuery(['staff-pick'], fetchFeaturedStaffPick)` — hero book
- `useQuery(['genre-sections'], fetchGenreSections)` — accordion data (genre name, book count, books array)

**Scroll Cards** show: cover image, title, author, star rating, availability badge, and item type badge (for non-book items like DVDs/audiobooks).

#### Search Mode

When a user submits a search from the nav bar, the page transitions to a grid results view:

**State**:
- `searchQuery: string` — bound to nav search input
- `selectedGenre: string | null` — genre filter chip
- `selectedItemType: string | null` — item type filter (book/audiobook/dvd/ebook/magazine)
- `sortBy: string` — sort option (relevance/title/rating/year)
- `page: number` — current page

**Data Fetching (Search)**: `useQuery(['books', { q, genre, item_type, sort, page }], fetchBooks)`
- Debounce search input by 300ms
- Update URL search params for shareable URLs (`/?q=science+fiction&genre=sci-fi`)

**UX Details**:
- Search triggers on Enter key or after 300ms debounce
- Genre chips are toggleable (click to select, click again to deselect)
- Results shown in a card grid with pagination (20 per page)
- Clear search → returns to Browse mode
- Loading: show skeleton cards while fetching
- Empty: "No books match your search. Try different keywords."

---

### BookDetailPage (`/books/:id`)

**Mockup**: `mockups/book-detail.html` — Classic 2-column layout

**Layout**: Two-column on desktop (cover 40% left, metadata 60% right), single column on mobile.

**Left Column**:
- Book cover in white card with border-radius 16px, centered, shadow
- Staff Pick badge below cover (if `is_staff_pick`): coral border card with gradient "Staff Pick" pill + librarian's note quote

**Right Column**:
- Title (Space Grotesk, 36px, 700)
- Author link (coral, dashed underline) — clicking navigates to `/?author=AuthorName`
- Star rating row (SVG stars, numeric rating, rating count)
- Genre pills (coral/blue alternating, rounded 50px)
- Metadata grid (2×3): Pages, Published, Format, Language, ISBN, Publisher — in a white bordered card
- Description section ("About this book")
- Availability badge (green pill with dot when available)
- Action buttons: "Check Out" (gradient pill) + "Reserve" (outlined pill)

**Breadcrumb** (contextual, below nav):
- From search: `Home > Search Results > [Title]` (uses `?from=search` query param)
- From genre accordion: `Home > [Genre] > [Title]` (genre links to `/?genre=X`, uses `?from=genre&genre=X` param)
- Direct nav: `Home > [Title]`
- Implementation: read `from` query param or referrer; default to direct nav

**Post-Action Inline Banners** (replaces action buttons after checkout/reserve):
- **Checkout success**: green tint (`rgba(16,185,129,.08)`), check icon, "Checked out! Due back [date]" + "View My Loans →" link + toast notification
- **Auto-reservation**: blue tint (`rgba(76,201,240,.08)`), info icon, "You're #N in the waitlist. We'll hold it 48h when available." + "View My Reservations →" link + toast
- **Fines block**: coral tint (`rgba(255,107,107,.08)`), warning icon, "Checkout paused — $X.XX in outstanding fines. [View Fines →]", button disabled
- **Loan limit**: coral tint, "Limit reached (N books). Return a book to check out more. [View My Loans →]", button disabled

**Below Two-Column**: Full-width Reviews section
- Left: Rating summary card (big number, star row, distribution bars with gradient fills)
- Right: Review card list (avatar circle, name, date, stars, review text)
- Write a Review form (star selector + textarea + gradient Submit button)

**"More by [Author Name]"** (below Reviews section):
- Horizontal scroll row reusing ScrollCard component
- Data: `useQuery(['books-by-author', author], () => apiFetch('/books', { params: { author, limit: '10' } }))`
- Hidden if only 1 book by that author in the catalogue
- Header: "More by [Author Name]" (Space Grotesk 22px 700)

**Data Fetching**:
- `useQuery(['book', id], fetchBookDetail)` — book data with availability
- `useQuery(['book-reviews', id], fetchBookReviews)` — reviews (separate for caching)

**Conditional UI**:
- **Not logged in**: "Check Out" button → redirects to sign-in
- **Logged in, book available, no existing loan**: "Check Out" button (active)
- **Logged in, book available, already checked out by user**: "You have this book" info
- **Logged in, all copies out**: "Reserve (Position #N)" or "Join Waitlist"
- **Logged in, has reservation**: "Cancel Reservation" button
- **User has a returned loan + no review**: "Write a Review" prompt

---

### LoansPage (`/loans`)

**Mockup**: `mockups/loans.html` — Data table with status pills

**Layout**: Data table in a white rounded card (16px radius), sorted by due date (earliest first).

**Table Structure**:
- Wrapper: white card with 1px border, 16px border-radius, subtle shadow
- Header row: dark (`#0d1117`) background, white text, Space Grotesk font, uppercase 13px
- Alternating row backgrounds (white / `#fafafa`), hover highlight (`#f0f4ff`)
- Columns: **Book** (cover thumbnail + title + author), **Checked Out**, **Due Date**, **Status**, **Renewals**, **Action**

**Book Cell**: 44×62px cover image + title (Space Grotesk 700) + author (13px muted)

**Status Pills** (rounded 50px, 12px bold):
- `active` → green tint background, green text — when `days_remaining > 3`
- `due-soon` → yellow tint, yellow text — when `0 <= days_remaining <= 3`
- `overdue` → red tint, red text — when `days_remaining < 0` (i.e., past due date)

**Due-soon threshold logic** (computed from `days_remaining`):
```typescript
function getLoanStatus(days_remaining: number): 'active' | 'due-soon' | 'overdue' {
  if (days_remaining < 0) return 'overdue';
  if (days_remaining <= 3) return 'due-soon';
  return 'active';
}
```

**Action Column**: "Renew" link (coral, 600 weight) or disabled "Renew" button (gray `#e5e5e5` background, `cursor: not-allowed`, 50px radius) with reason text below in muted 11px (e.g., "Max renewals reached", "Reservation exists")

**Renew Flow**:
1. Click "Renew" → optimistic UI (show "Renewing...")
2. Call `POST /api/loans/:id/renew`
3. On success: update due date, show toast "Renewed until [date]"
4. On error: show toast with error message ("Cannot renew — someone is waiting")

**Review Nudge** (top-most, above table, dismissible): If user has a returned book (last 7 days) with no review: subtle card with "How was **[Book Title]**? Your rating helps other readers. [Rate it →]" and X dismiss button. localStorage tracks dismissed book_ids. Only show for the most recent unreviewed return.

**Ready Reservation Alert** (below nudge, above table): green tint banner (`rgba(16,185,129,.08)`), bell icon, "Your reservation for **[Title]** is ready! Pick up by [date] (Xh remaining)" + "Check Out Now →" link. One banner per ready reservation.

**Overdue Alert** (below ready alert, above table): coral tint (`rgba(255,107,107,.08)`), warning icon, "You have **N** overdue book(s). Return to avoid fines. Accrued: **$X.XX**"

**Return Info Banner** (below table): Light blue tint, info icon, text: "Returns are processed by library staff. Bring physical copies to the front desk; for digital items, contact the library."

**Nav Badge**: Coral dot (8px) on "My Loans" nav link when any reservation is ready. Layout component fetches reservations for signed-in users.

**Empty State**: "No active loans. [Browse the catalogue] to find your next read!"

**Data**: `useQuery(['my-loans'], fetchMyLoans)`

#### Reservations Section (below loans table)

**Layout**: "My Reservations" header + reservation cards in a white rounded card.

**Reservation Cards**:
- Book info (thumbnail + title + author)
- Status pill: `pending` → blue tint background (`rgba(76,201,240,.1)`) + blue text (`#4cc9f0`); `ready` → green tint background (`rgba(16,185,129,.1)`) + green text (`#10b981`)
- Queue position (if pending): "Position #2 in waitlist"
- Pickup deadline (if ready): "Pick up by Mar 12, 2026" with countdown
- "Cancel" link (coral)

**Data**: `useQuery(['my-reservations'], fetchMyReservations)`

**Empty State**: "No active reservations."

---

### HistoryPage (`/history`)

**Mockup**: `mockups/history.html` — Data table with month group rows

**Layout**: Data table in a white rounded card (16px radius), paginated.

**Table Structure**:
- Wrapper: white card with 1px border, 16px border-radius
- Header row: `#fafafa` background, uppercase 12px column headers (muted gray)
- **Month group rows** span the full table width with Space Grotesk 700, 15px, `#fafafa` background (e.g., "March 2026", "February 2026")
- Columns: **Book** (42×60px cover + title + author), **Borrowed**, **Returned**, **Action**, **Review**, **Fine**

**Book Cell**: 42×60px cover (border-radius 8px, gradient placeholder if no image) + title (Space Grotesk 700, 14px) + author (13px muted)

**Action Column**: "Borrow Again" coral link → `/books/:id` when book exists, or muted "Unavailable" text when book deleted

**Review Nudge** (above table, dismissible): Same as LoansPage — dismissible card for most recent unreviewed return.

**Review Column**: Star display (gold `#f59e0b`) if reviewed, or "Write Review" link (coral, 600 weight) if not

**Fine Column**: Right-aligned. Em-dash if none, or red amount (e.g., "$1.50") for late returns. Late rows get subtle red tint (`rgba(255,107,107,.02)`)

**Pagination**: Centered below table. "← Previous" / "Page X of Y" / "Next →". Disabled link style for boundaries.

**Data**: `useQuery(['loan-history', page], fetchLoanHistory)`

---

### FinesPage (`/fines`)

**Mockup**: `mockups/fines.html` — Stat cards + data table

**Layout**: Outstanding balance display at top, optional warning banner, then data table.

**Outstanding Balance Display**:
- Single prominent amount: Space Grotesk 700 40px, coral if > $0, green if $0
- Label above: "Outstanding Balance" (12px uppercase muted)
- If $0: green amount + "All clear — no outstanding fines" subtitle (green, 14px)
- If > $0: coral amount + "[N] pending fine(s)" subtitle (muted, 14px)
- White card, 16px radius, centered, 32px vertical padding

**Warning Banner** (shown when balance >= $10.00): Light red tint background, coral border, warning icon circle + bold message text

**Fines Table**:
- Wrapper: white card with 16px radius, "Fine History" header inside card
- Header row: uppercase 12px, muted gray, with right-aligned last column
- Columns: **Book** (cover thumbnail + title + author — matching the loans/history table pattern), **Reason** (pill badge, gray background), **Amount** (Space Grotesk 700 — red for pending, green for paid, gray for waived), **Status** (pills — red/green/gray), **Date**
- Pending rows get subtle red tint (`rgba(255,107,107,.03)`)
- Date column shows accrual details for pending fines (e.g., "14 days × $0.25/day")

**Payment Info** (below table): Info text with icon: "Visit the library front desk to pay outstanding fines. We accept cash and card payments. Balances of $10 or more will prevent new checkouts."

**Note**: Fine records only exist for returned books. For active overdue loans, the accruing fine is displayed inline on the LoansPage (calculated on-the-fly, not stored as a record).

**Data**: `useQuery(['my-fines'], fetchMyFines)`

---

### AIAssistantPage (`/ai-assistant`)

**Mockup**: `mockups/settings.html` — Setup guide + table + modal overlay

**Layout**: Page header + Setup Guide + API Keys section + Example Prompts.

**Page Header**: "AI Assistant" (Space Grotesk 32px 700) + subtitle "Connect your AI assistant to PageTurn"

**Setup Guide** (white card, 16px radius, above API keys):
- Numbered steps in a vertical list:
  1. Generate an API key below
  2. Open Claude Desktop → Settings → MCP
  3. Paste the configuration (shown in code block)
  4. Restart Claude Desktop
- Code block (`#0d1117` background, 14px monospace) showing full `claude_desktop_config.json` with MCP URL pre-filled:
  ```json
  {
    "mcpServers": {
      "pageturn": {
        "url": "https://mcp.pageturn.app/user",
        "headers": {
          "Authorization": "Bearer YOUR_API_KEY"
        }
      }
    }
  }
  ```
- "Copy Config" gradient button (same style as Generate Key button)
- Platform-specific config file paths below code block (muted 13px):
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - Linux: `~/.config/Claude/claude_desktop_config.json`

**API Keys Section**:
- Section header: "API Keys" h2 + gradient "Generate New Key" button (right-aligned)
- Table in white card (16px radius): columns **Name** (600 weight), **Key Prefix** (monospace in gray pill), **Scope** (blue tint badge), **Last Used** (green "2 hours ago" or gray italic "Never"), **Created** (muted date), **Revoke** (coral link)
- Info text below table with info icon: explains what API keys are for

**Generate Key Modal** (overlay with blur backdrop):
- White card, 500px max-width, 16px radius, deep shadow
- Form fields: Key Name (text input with `#fafafa` background, 12px radius, blue focus border), Scope (radio group: User only for regular members; User / Admin for admin users)
- **Key Reveal State** (shown after generation): green success label with checkmark, dark code box (`#0d1117` background) showing key in cyan monospace with "Copy" button, red warning message "Save this key now. You won't be able to see it again."
- Modal actions: "Close" button (outlined pill)

**API Key Generation Flow**:
1. Click "Generate New Key" → modal opens with form
2. Enter name, select scope → Submit
3. `POST /api/api-keys` → response includes full key
4. Modal transitions to reveal state showing the key
5. User copies key → closes modal → key row appears in table (prefix only)

**Example Prompts** (below API keys, 3-column card grid):
- Each card: white background, 16px radius, subtle border, 16px padding
- Cards:
  1. "What books do I have checked out?"
  2. "Recommend a mystery novel set in London"
  3. "Check out Dune for me"
- Style: DM Sans 14px 500, muted icon top-left, coral quote marks

---

### MyReviewsPage (`/reviews`)

**Layout**: Page header + review cards list.

**Page Header**: "My Reviews" (Space Grotesk 32px 700) + subtitle "[N] reviews written" (muted count)

**Review Cards** (not a table — card-based layout):
- Each card: white background, 16px radius, 1px border, 20px padding, subtle shadow
- Left side: book cover thumbnail (48×68px, 8px radius) + title (Space Grotesk 600 15px) + author (DM Sans 13px muted)
- Center: star rating display (gold `#f59e0b`), review text (DM Sans 14px, max 3 lines with "Show more" expand), date (muted 12px)
- Right side: Edit (muted link) | Delete (coral link) actions

**Edit Flow**:
- Click Edit → card expands to inline edit mode
- Star selector (clickable stars) + textarea (pre-filled with existing text) + Save/Cancel buttons
- Save: `POST /api/reviews` (upsert) → invalidate queries → collapse back to display mode

**Delete Flow**:
- Click Delete → confirmation toast: "Delete this review?" with Undo action (3 second window)
- `DELETE /api/reviews/:id` → invalidate queries → card removed

**Empty State**: "No reviews yet. Rate books you've borrowed to help other readers." + "Browse Catalogue" CTA button (gradient pill → `/`)

**Data**: `useQuery(['my-reviews'], fetchMyReviews)`

---

### Admin Pages — Design System ("Notion/Stripe" Style)

Admin pages use a **distinct, denser design** from user-facing pages. The philosophy: admins don't care about pretty — they need information density, fast actions, and zero wasted space.

**Mockups**: `mockups/admin-dashboard.html`, `admin-books.html`, `admin-users.html`, `admin-user-detail.html`, `admin-fines.html`

**Important**: The mockups represent the approved **layout and visual style** (density, sidebar, KPI bars, table patterns, hover actions). The implementation must follow BOTH the mockups for look-and-feel AND the full spec below for all behaviors, data fetching, edge cases, modals, and business logic. The mockups are style references, not feature-complete specs.

**Admin Design Tokens** (override user-facing tokens):
- Body font size: 13px (not 14px)
- Background: `#f9fafb` (slightly cooler than user `#fafafa`)
- Nav height: 48px (not 72px) — compact
- Card radius: 6-8px (not 16px) — less decorative
- Table row height: 44px fixed
- No stat cards — use KPI bar instead
- Status: 6px colored dot + text (not rounded pill badges)
- Actions: ghost buttons that appear on row hover (not always-visible links)
- Amounts: Space Grotesk 600, `font-variant-numeric: tabular-nums`, right-aligned

**AdminLayout**:
- Collapsed icon sidebar (48px, dark `#1e2330`) + content area
- Sidebar expands to 200px on hover, showing labels via CSS transition
- Sidebar icons: grid (dashboard), book (books), users (users), dollar (fines)
- Active link: white text, coral left border (2px), subtle lighter background
- No footer on admin pages (tool-like, not marketing)

**KPI Bar** (replaces stat cards on all admin pages):
- Full-width white bar below nav, with `border-bottom: 1px solid #e5e7eb`
- Metrics side by side, divided by thin vertical lines
- Each metric: 11px uppercase muted label, 24px Space Grotesk 700 value (colored), 12px muted subtitle
- Compact: 14px vertical padding

**Controls Row** (on table pages):
- Left: underline filter tabs (text, not pills) — active = bold + bottom border
- Right: compact search input (200px, 32px height) + action buttons (32px height, 6px radius)

**Table Pattern** (consistent across all admin pages):
- No card wrapper — table IS the content
- Header: 11px uppercase `#6b7280`, `letter-spacing: 0.5px`, bottom border only
- Sort arrows (▲▼) on sortable columns
- 44px row height, `border-bottom: 1px solid #f3f4f6`
- Hover: coral left border (2px) + subtle background tint
- Ghost action buttons: invisible by default, appear on row hover with coral color

**AdminDashboard** (`/admin`):
- KPI bar: Total Books, Total Copies, Active Loans, Overdue, Users, Fines Outstanding
- Split content: Recent Activity table (60%) + Overdue list + Quick Actions (40%)
- Recent Activity: Time, Event, User, Details columns
- Quick Actions: "Process Returns", "View Overdue", "Manage Fines" — outlined 32px buttons

**AdminBooksPage** (`/admin/books`):
- KPI bar: Total Books, Total Copies, Staff Picks, Avg Rating
- Filter tabs: All, Books, Audiobooks, DVDs, Ebooks, Magazines
- Table: Title, Author, Genre (plain text), Type (muted text), Copies (blue clickable), Rating, Staff Pick ("Yes" coral or dash), Actions (Edit/Delete ghost buttons)
- Add Book modal: 560px, 8px radius, dense 2-column form, 32px inputs, 11px labels
- Clicking copy count opens **CopyManagementModal** with copy table (Barcode, Condition, Status, Actions)

**AdminUsersPage** (`/admin/users`):
- KPI bar: Total Users, Admins, Active Borrowers, Blocked (fines >= $10)
- Filter tabs: All, Active, Admins, Blocked
- Table: Name, Email, Role ("admin" coral / "user" muted), Active Loans, Outstanding Fines (coral if > 0), Max Loans, Joined
- No avatars — density over decoration
- Clickable rows → navigate to `/admin/users/:id`

**AdminUserDetail** (`/admin/users/:id`):
- KPI bar: Active Loans, Total Borrowed, Outstanding Fines, Reviews Written, Max Loans
- User info bar: name + role + email + join date (compact horizontal), Edit/Promote buttons right-aligned
- Breadcrumb: "Users" → "Mike Chen"
- Tab bar (underline style): Loans, History, Reservations, Fines, Reviews
- Current Loans table: Book, Checked Out, Due Date, Status (dot), Renewals (#/2), Action (Return/Mark Lost ghost buttons)
- Fines section below: compact table with Waive ghost buttons, total outstanding right-aligned

**AdminFinesPage** (`/admin/fines`):
- KPI bar: Outstanding, Collected, Waived, Avg Fine
- Filter tabs: All, Pending, Paid, Waived
- Table: User, Book, Reason (plain text), Amount (right-aligned), Status (dot), Date, Action (Waive ghost button)
- Sort arrows on Amount and Date

---

## Shared Components

### `SearchBar`
- Input with search icon
- Optional clear button when text is entered
- Debounced onChange (300ms)
- Enter key triggers immediate search

### `BookCard`
- Cover image with fallback (gray placeholder with book icon if image fails to load)
- Title (truncated to 2 lines)
- Author (truncated to 1 line)
- Star rating display
- Genre tag pill
- Availability badge (green/orange/red)

### `StarRating`
- Display mode: filled/empty stars based on rating
- Input mode: clickable stars for review form

### `AvailabilityBadge`
- Green (`#10b981`): "Available" or "Available — N copies"
- Orange/Warning (`#f59e0b`): "Due [date]" or "All copies out" — used on browse cards and book detail when no copies are available
- Blue (`#4cc9f0`): "You have this book"
- Red (`#ff6b6b`): "Overdue" — only for the user's own overdue loans

**Important**: On homepage browse cards, unavailable books use the **orange** warning color, not red/coral.

### `ItemTypeBadge`
- Small pill shown on book cards and detail pages for non-book item types
- Only displayed for: audiobook, dvd, ebook, magazine (not shown for 'book' — it's the default)
- Style: muted gray background pill with icon (headphones for audiobook, disc for DVD, tablet for ebook, newspaper for magazine)
- On book detail: shown in the metadata grid as "Format" field

### `GenreTag`
- Small pill/chip with genre text
- Color can vary by genre (optional, design-dependent)

### `Pagination`
- "← Previous | Page X of Y | Next →"
- Direct page number links for nearby pages

### `ProtectedRoute`
- Wraps `<SignedIn>` from Clerk
- Shows sign-in prompt for unauthenticated users
- `AdminOnly` variant also checks role from user metadata

### `Toast`
- Non-blocking notification at bottom-right
- Auto-dismiss after 3 seconds
- Variants: success (green), error (red), info (blue)

### `Modal`
- Overlay with centered content
- Close on Esc key or backdrop click
- Used for: book form, key reveal, confirmations

### `EmptyState`
- Centered illustration/icon
- Message text
- Optional CTA button

### `LoadingSkeleton`
- Pulsing placeholder blocks matching the shape of the content
- Used during data fetching

### Error Handling UX

- **Transient errors** (network failures, server 500s): Show a toast notification at bottom-right. Auto-dismiss after 3 seconds. Red variant for errors.
- **Form validation errors** (review submission, checkout blocks): Show inline error messages below the relevant form field or action button. Use `--color-error` text color.
- **Checkout/renewal blocks** (fines, reservation conflicts, max loans): Show a dismissible inline banner above the action area with the specific reason and any next steps (e.g., "Resolve fines" link).
- **Empty states** are not errors — use the `EmptyState` component with helpful CTAs.

### Footer

- Background: `#0d1117` (matches nav bar)
- Layout: flex row with logo/tagline on left, nav links center, copyright spanning full width below
- Content: PageTurn logo (gradient "Turn"), tagline "Your modern library catalogue", links (Browse, My Loans, Privacy, Terms), copyright "2026 PageTurn Library"
- Consistent across all pages via the Layout component

---

## API Client (`lib/api.ts`)

```typescript
const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function apiFetch<T>(
  path: string,
  options?: RequestInit & { params?: Record<string, string> }
): Promise<T> {
  const { params, ...fetchOptions } = options || {};

  let url = `${API_BASE}${path}`;
  if (params) {
    const searchParams = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null)
    );
    url += `?${searchParams}`;
  }

  // Get Clerk token
  const token = await window.Clerk?.session?.getToken();

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...fetchOptions?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail);
  }

  return response.json();
}
```

---

## React Query Hooks (`hooks/`)

```typescript
// hooks/useBooks.ts
export function useBookSearch(params: BookSearchParams) {
  return useQuery({
    queryKey: ['books', params],
    queryFn: () => apiFetch('/books', { params }),
    staleTime: 30_000,  // 30s — books don't change often
  });
}

export function useBookDetail(bookId: string) {
  return useQuery({
    queryKey: ['book', bookId],
    queryFn: () => apiFetch(`/books/${bookId}`),
  });
}

// hooks/useLoans.ts
export function useMyLoans() {
  return useQuery({
    queryKey: ['my-loans'],
    queryFn: () => apiFetch('/loans'),
  });
}

export function useRenewLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (loanId: string) => apiFetch(`/loans/${loanId}/renew`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-loans'] }),
  });
}

export function useCheckout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (bookId: string) => apiFetch('/loans', {
      method: 'POST',
      body: JSON.stringify({ book_id: bookId }),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-loans'] });
      queryClient.invalidateQueries({ queryKey: ['book'] });
    },
  });
}
```

---

## TypeScript Types (`types/index.ts`)

```typescript
export interface Book {
  id: string;
  title: string;
  author: string;
  isbn?: string;
  isbn13?: string;
  description?: string;
  genre?: string;
  genres: string[];
  item_type: 'book' | 'audiobook' | 'dvd' | 'ebook' | 'magazine';
  cover_image_url?: string;
  page_count?: number;
  publication_year?: number;
  publisher?: string;
  language: string;
  avg_rating: number;
  rating_count: number;
  available_copies: number;
  total_copies: number;
  is_staff_pick: boolean;
  staff_pick_note?: string;
}

export interface BookDetail extends Book {
  copies: BookCopy[];
  earliest_return_date?: string;
  reservation_count: number;
  user_loan?: Loan;
  user_reservation?: Reservation;
}

export interface BookCopy {
  id: string;
  status: 'available' | 'checked_out' | 'reserved' | 'damaged' | 'lost';
  condition: 'new' | 'good' | 'fair' | 'poor';
}

export interface Loan {
  id: string;
  book: BookSummary;
  checked_out_at: string;
  due_date: string;
  returned_at?: string;
  days_remaining: number;
  renewed_count: number;
  can_renew: boolean;
  renewal_blocked_reason?: string;
  status: 'active' | 'returned' | 'overdue';
  accrued_fine?: number;
  daily_rate?: number;
  days_overdue?: number;
}

export interface Reservation {
  id: string;
  book: BookSummary;
  status: 'pending' | 'ready' | 'fulfilled' | 'expired' | 'cancelled';
  queue_position?: number;
  expires_at?: string;
  reserved_at: string;
}

export interface Fine {
  id: string;
  book_title: string;
  book_author: string;
  book_cover_url?: string;
  loan_id: string;
  amount: number;
  daily_rate: number;
  days_overdue: number;
  reason: 'late_return' | 'lost_item' | 'damaged_item';
  status: 'pending' | 'paid' | 'waived';
  created_at: string;
}

export interface Review {
  id: string;
  user_name: string;
  user_initial: string;
  rating: number;
  review_text?: string;
  created_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'user' | 'admin';
  max_loans: number;
  active_loan_count: number;
  outstanding_fines: number;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scope: 'user' | 'admin';
  last_used_at?: string;
  created_at: string;
  is_active: boolean;
}

interface BookSummary {
  id: string;
  title: string;
  author: string;
  cover_image_url?: string;
}

// NOTE: There is no generic PaginatedResponse<T>. Each API endpoint uses
// domain-specific response keys (e.g., "books", "loans", "fines", "reviews").
// Define per-endpoint response types instead (e.g., BooksResponse, LoansResponse)
// that match the actual JSON shape returned by each endpoint. See API.md for
// the exact response structures.
```

---

## Package Dependencies

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.22.0",
    "@clerk/clerk-react": "^5.0.0",
    "@tanstack/react-query": "^5.20.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    "vite": "^5.1.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## Vercel Configuration

```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://api.pageturn.app/api/:path*" }
  ]
}
```

Frontend and API are deployed as separate Vercel projects. The frontend proxies `/api/*` requests to the backend.

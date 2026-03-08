# PageTurn — Business Summary

*A modern library catalogue and management system*

---

## What Is PageTurn?

PageTurn is a web-based library management system that lets anyone browse a catalogue of 1,000+ books, and lets registered members check out books, manage loans, and get AI-powered reading recommendations. Administrators get a full management dashboard to oversee the library's operations.

---

## Who Uses It?

### Visitors (No Account)
Anyone can visit the website and search the full catalogue. They can see book details, availability, and community reviews — no sign-up required.

### Members (Free Account)
Members sign in with their Google account or email. They can:
- **Check out books** — instantly if available
- **Join a waitlist** — if the book is currently checked out by someone else
- **Manage their loans** — see due dates, renew books, view history
- **See their fines** — transparent breakdown of any late fees
- **Rate and review books** — leave star ratings and written reviews
- **Get AI recommendations** — connect an AI assistant that knows their reading history

### Administrators
Admins manage the library through a dedicated dashboard:
- **Add, edit, and remove books** from the catalogue
- **Manage user accounts** — view loans, handle disputes
- **Waive fines** — forgive late fees when appropriate
- **Access an AI admin assistant** — for quick lookups and bulk operations

---

## Key Features

### 1. Smart Book Search
The search bar is the centerpiece. Users type a title, author name, or genre and get instant results. They can also filter by genre and item type (book, audiobook, DVD, ebook, magazine). Search results show cover art, ratings, and real-time availability.

### 2. Real-Time Availability
Every book shows whether it's available right now. If it's checked out, users can see when it's expected back. This information updates in real time as books are checked out and returned.

### 3. Checkout & Reservations
- **Available books**: One click to check out. The due date is set automatically based on the item type (14 days for books, 7 for DVDs, 21 for audiobooks).
- **Unavailable books**: Users join a waitlist. When the book is returned, the next person in line gets notified and has 48 hours to pick it up.
- **Fair renewals**: Members can renew a loan up to 2 times — unless someone else is waiting for the book. This ensures fair access.

### 4. Transparent Fine System
Late returns incur a small daily fee ($0.25/day for books, $1.00/day for DVDs). Fines are capped at $25 per item so they never become unreasonable. Users can see exactly how their fines are calculated. Admins can waive fines when circumstances warrant it.

If a member has $10 or more in unpaid fines, they can't check out new books until the balance is resolved.

### 5. Community Reviews & Ratings
Members can rate books (1-5 stars) and leave written reviews for any book they've borrowed. These reviews are public and help other members decide what to read. Average ratings appear on every book card in search results.

### 6. AI Library Assistant
This is the standout feature. Members and admins can connect an AI assistant (like Claude) to their library account through a secure API. The AI can:

**For members:**
- Search the catalogue conversationally ("Find me a mystery novel set in London")
- Check loan status ("What books do I have out? When are they due?")
- Make recommendations based on reading history and past reviews
- Check out and reserve books on the user's behalf

**For admins:**
- Look up user accounts and their loan history
- Find all overdue books
- Waive fines
- Get library statistics

The AI doesn't store any data — it accesses the library system in real time through secure API tools, using the same permissions the user would have on the website. Setting up is simple: generate an API key from the AI Assistant page, copy the configuration into Claude Desktop, and start chatting. Example prompts are provided to get started.

### 7. Admin Dashboard
A dedicated admin panel with:
- **Overview stats**: Total books, active loans, overdue count, total fines
- **Book management**: Add new books with full metadata (title, author, ISBN, genre, cover image, description, etc.), edit existing entries, remove books
- **User management**: View all members, see their loan and fine history, manage their accounts
- **Fine management**: View all outstanding fines, waive individual fines or batch waive

---

## How It Works (Technical Summary for Non-Technical Readers)

- **Website**: Works in any web browser, on desktop and mobile
- **Sign-in**: Uses Google or email sign-in — no separate library card or password to remember
- **Data**: The catalogue starts with 1,000+ real books with covers, descriptions, and metadata
- **AI integration**: Uses the Model Context Protocol (MCP), an open standard that lets AI assistants connect to external services securely
- **Security**: User data is protected. AI access requires an API key that can be revoked at any time. Admins are promoted through a controlled process.

---

## What Makes PageTurn Special?

1. **No friction**: Browse without an account. Sign in with one click. Check out in seconds.
2. **AI-native**: Not just a website with AI tacked on — the AI assistant is deeply integrated, understanding your full reading history and preferences.
3. **Fair by design**: The reservation system, renewal blocking, and fine caps all ensure equitable access to the library's collection.
4. **Real library operations**: Mock data simulates a real library with active users, ongoing loans, waitlists, and fines — it's not an empty demo.
5. **Admin empowerment**: Admins get both a visual dashboard and an AI assistant, so they can handle routine tasks quickly.

---

## Numbers at a Glance

| Metric | Value |
|--------|-------|
| Books in catalogue | 1,000+ |
| Mock users | 50 |
| Mock loan records | 500+ |
| Mock reviews | 200+ |
| Loan period (books) | 14 days |
| Max renewals | 2 per loan |
| Daily late fee (books) | $0.25 |
| Fine cap per item | $25.00 |
| Reservation hold time | 48 hours |
| Max concurrent loans | 5 per user |

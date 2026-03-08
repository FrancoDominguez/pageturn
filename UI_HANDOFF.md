# PageTurn — UI Handoff Notes

## Mockup Inventory

### User-Facing Pages (Bold Modern design)
- `mockups/option-c4-home.html` — Homepage (browse + search)
- `mockups/book-detail.html` — Book detail page
- `mockups/loans.html` — My Loans page
- `mockups/history.html` — Loan History page
- `mockups/fines.html` — Fines page
- `mockups/settings.html` — AI Assistant / API Keys page

### Admin Pages (Notion/Stripe dense design)
- `mockups/admin-dashboard.html` — Dashboard with KPI bar, activity table, quick actions
- `mockups/admin-books.html` — Books table with Add Book modal
- `mockups/admin-users.html` — Users table with role labels, clickable rows
- `mockups/admin-user-detail.html` — User profile, loans tab, fines with waive buttons
- `mockups/admin-fines.html` — Fines table with filter tabs, KPI bar

## Design System Notes

**User pages** and **admin pages** use different design approaches:

| | User Pages | Admin Pages |
|---|---|---|
| Philosophy | Friendly, spacious, visual | Dense, functional, information-first |
| Nav height | 72px | 48px |
| Body font | 14px | 13px |
| Card radius | 16px | 6-8px |
| Sidebar | None (sub-nav tabs) | 48px collapsed icon bar, expands on hover |
| Stats | Rounded cards with colored borders | KPI bar with vertical dividers |
| Status | Rounded pill badges | 6px colored dot + text |
| Table actions | Always-visible coral links | Ghost buttons, appear on hover |
| Footer | Yes (dark, matches nav) | No footer |

Both share: Space Grotesk headings, DM Sans body, coral (#ff6b6b) primary, PageTurn gradient logo.

# PageTurn — How to Edit the PRDs and Implementation Docs

This project has 8 interconnected documentation files. When you change something, multiple files may need updating. This guide explains the structure, what lives where, and how changes cascade.

---

## Document Map

```
ARCHITECTURE.md          ← High-level overview (read first, rarely edited)
├── docs/PRD.md          ← Features and acceptance criteria
├── docs/DATABASE.md     ← SQL schema, indexes, triggers, seed data
├── docs/API.md          ← REST endpoints and response contracts
├── docs/FRONTEND.md     ← Components, pages, types, design tokens
├── docs/MCP.md          ← MCP server tools and auth
├── docs/DEPLOYMENT.md   ← Infra setup and CLI commands
└── docs/IMPLEMENTATION.md ← Master build guide (references all above)

AGENT_INSTRUCTIONS.md    ← Handoff for the implementation agent
MANUAL_SETUP.md          ← Manual steps the user must complete
UI_HANDOFF.md            ← Context for UI mockup work
```

---

## Change Cascade Rules

Different types of changes touch different files. Use this table:

| Change Type | Files to Update |
|-------------|----------------|
| **New feature** | PRD.md → DATABASE.md → API.md → FRONTEND.md → IMPLEMENTATION.md |
| **Modify existing feature** | PRD.md → (any downstream file the change affects) |
| **UI/design change** | FRONTEND.md only (page specs, component tree, design tokens) |
| **New DB table or column** | DATABASE.md → API.md (if exposed) → FRONTEND.md (TypeScript types) → IMPLEMENTATION.md (model + migration notes) |
| **New API endpoint** | API.md → FRONTEND.md (hooks + types) → IMPLEMENTATION.md (phase 2 checklist) |
| **New MCP tool** | MCP.md → API.md (if it needs a new endpoint) |
| **Seed data change** | DATABASE.md (seed spec section) → IMPLEMENTATION.md (phase 3) |
| **Deployment/infra change** | DEPLOYMENT.md → IMPLEMENTATION.md (phase 6) |

---

## File-by-File Editing Guide

### `docs/PRD.md` — Features and Requirements

**Structure**:
```
## 1. Product Overview
## 2. User Roles (Visitor, Member, Admin)
## 3. Feature Specifications
    ### F1: Book Search & Browse
    ### F2: Book Detail Page
    ... through F16
## 4. Non-Functional Requirements
## 5. Mock Data
## 6. Out of Scope
```

**To add a new feature**:
1. Find the last feature number (currently F16)
2. Add a new `### F17: Feature Name` section with:
   - **Priority**: P0 (Core) / P1 (Important) / P2 (Nice to have) / Low
   - **Description**: 2-3 sentences
   - **Acceptance Criteria**: Checkbox list (`- [ ] ...`)
3. Add a `---` separator after it
4. Then cascade the change to other files (see table above)

**To modify a feature**:
- Edit the acceptance criteria checkboxes
- Update the description if scope changed
- Check if the change affects the DB schema, API, or frontend

**To add/modify mock data requirements**:
- Edit the `## 5. Mock Data` section
- Update specific numbers (e.g., "75 active loans" → "100 active loans")
- Make sure DATABASE.md seed specs match

**Example** (adding Staff Picks was done like this):
```markdown
### F15: Staff Picks
**Priority**: Medium
**Description**: Admins can mark books as "Staff Picks" with a personal note...

**Acceptance Criteria**:
- [ ] Books can be marked/unmarked as staff picks by admins
- [ ] Each staff pick has an optional note
- [ ] Homepage displays a featured staff pick in hero section
- [ ] Staff picks filterable via API
- [ ] Admin panel toggle for staff pick status
```
Then: added `is_staff_pick` + `staff_pick_note` to DATABASE.md, added `staff_picks` query param to API.md, added fields to FRONTEND.md TypeScript types.

---

### `docs/DATABASE.md` — Schema and Seed Data

**Structure**:
```
## Entity Relationship Diagram
## Table Definitions (SQL)
    ### users
    ### books
    ### book_copies
    ### loans
    ### reservations
    ### fines
    ### reviews
    ### api_keys
## Utility Functions (triggers, stored functions)
## Seed Data Specification
    ### Books (from Kaggle CSV)
    ### Book Copies
    ### Users (mock)
    ### Loans (mock)
    ### Reservations (mock)
    ### Fines (mock)
    ### Reviews (mock)
## Alembic Configuration
```

**To add a column**:
1. Add it to the `CREATE TABLE` statement in the right position
2. Add an index if it will be queried frequently
3. Update the seed data spec if the column needs seeded values
4. Update FRONTEND.md TypeScript types
5. Update API.md response objects if exposed

**To add a table**:
1. Add a new `### table_name` section with full `CREATE TABLE` SQL
2. Add indexes
3. Update the ERD at the top
4. Add seed data spec if needed
5. Cascade to API.md, FRONTEND.md, IMPLEMENTATION.md

**To modify seed data**:
- Update the specific subsection (e.g., "### Loans (mock)")
- Change counts, distributions, or data generation rules
- Make sure PRD.md mock data section stays in sync

---

### `docs/API.md` — REST Endpoints

**Structure**:
```
## Authentication (Clerk JWT + API key flows)
## Public Endpoints
    ### GET /api/books
    ### GET /api/books/:id
    ### GET /api/books/:id/reviews
## User Endpoints (require auth)
    ### POST /api/loans
    ### GET /api/loans
    ... etc
## Admin Endpoints (require admin role)
    ### GET /api/admin/stats
    ... etc
## Webhook
    ### POST /api/webhooks/clerk
## Error Response Format
## CORS Configuration
```

**Each endpoint has**:
- Method + path
- Auth requirement (None / User / Admin / API Key)
- Query parameters table (if GET)
- Request body (if POST/PUT)
- Response JSON shape
- Error codes

**To add an endpoint**:
1. Add it under the right section (Public / User / Admin)
2. Include all fields: method, path, auth, params/body, response, errors
3. Update FRONTEND.md with a new React Query hook if the frontend calls it
4. Update IMPLEMENTATION.md phase 2 checklist
5. If the endpoint exposes new data, make sure the DB schema supports it

**To add a query parameter**:
- Find the endpoint's parameters table
- Add a new row: `| param_name | type | default | description |`

**To modify a response shape**:
- Update the JSON example
- Update FRONTEND.md TypeScript interfaces to match

---

### `docs/FRONTEND.md` — Frontend Specification

**Structure**:
```
## Design System (tokens, Tailwind config)
## Routing Table
## Component Tree
## Page Specifications
    ### HomePage
    ### BookDetailPage
    ### LoansPage
    ### HistoryPage
    ### FinesPage
    ### SettingsPage
    ### Admin Pages
## Shared Components
## API Client
## React Query Hooks
## TypeScript Interfaces
## Package Dependencies
## Vercel Configuration
```

**To update design tokens** (after mockup selection):
- Replace the CSS custom properties in the Design System section
- The Tailwind config references these variables, so only the `:root` block needs updating

**To update a page spec**:
- Find the page under `## Page Specifications`
- Update the layout description, data fetching, conditional UI, or UX details
- If the layout changed based on mockup selection, describe the chosen layout

**To add a TypeScript interface field**:
- Find the interface in the `## TypeScript Interfaces` section
- Add the field with its type
- Example: added `is_staff_pick: boolean;` and `staff_pick_note?: string;` to the `Book` interface

**To add a new page**:
1. Add a row to the Routing Table
2. Add the component to the Component Tree
3. Add a new `### PageName` under Page Specifications
4. Add any new hooks to the React Query section
5. Add any new types to TypeScript Interfaces

**To add a shared component**:
- Add it under `## Shared Components` with its props and behavior description

---

### `docs/IMPLEMENTATION.md` — Master Build Guide

**Structure**:
```
## Phase 0: Environment Setup
## Phase 1: Backend Foundation
## Phase 2: Core API
## Phase 3: Seed Data
## Phase 4: Frontend
## Phase 5: MCP Servers
## Phase 6: Deployment
## Phase 7: Admin Promotion & Verification
## Code Patterns to Follow
## Dependency Graph
```

**This is the step-by-step build guide**. Each phase lists exact files to create, in order, with code patterns.

**To add a new feature to the build**:
1. Identify which phase it belongs to (DB=Phase 1, API=Phase 2, Seed=Phase 3, Frontend=Phase 4, MCP=Phase 5)
2. Add the new file(s) to the appropriate phase's file list
3. Add any new dependencies
4. Update the Dependency Graph if the feature affects build order

**To modify phase instructions**:
- Find the phase section
- Update the file list, code patterns, or verification steps
- Keep the structure: what to create → how to create it → how to verify it works

---

### `docs/MCP.md` — MCP Server Specification

**Structure**:
```
## Architecture
## Authentication (API key flow)
## Claude Desktop Configuration
## Server Implementation Pattern
## User Tools (12 tools)
## Admin Tools (9 additional tools)
## Recommendation Strategy
## Deployment (Dockerfile, Cloud Run)
```

**To add a new MCP tool**:
1. Add it to the User Tools or Admin Tools section
2. Include: tool name, description, parameters (with types), return type
3. If the tool needs a new API endpoint, add that to API.md first
4. Update the tool count in the section header

---

### `docs/DEPLOYMENT.md` — Infrastructure

Rarely needs editing unless:
- Adding a new service (add deployment commands)
- Changing hosting (update CLI commands)
- Adding environment variables (update the env var tables)

---

### `ARCHITECTURE.md` — High-Level Overview

This is a summary document. Only edit it if:
- The tech stack changes
- The overall system architecture changes
- New major components are added

---

## Common Editing Scenarios

### "User wants to add a new page to the frontend"

1. `docs/PRD.md` — Add feature spec if it's a new feature
2. `docs/API.md` — Add any new endpoints the page needs
3. `docs/FRONTEND.md` — Add route, component tree entry, page spec, hooks, types
4. `docs/IMPLEMENTATION.md` — Add to Phase 4 file list
5. Create mockup HTML in `mockups/` for user to review

### "User wants to change how a page looks"

1. Create new mockup variation(s) in `mockups/`
2. After selection: update `docs/FRONTEND.md` page spec only
3. No other files need changing (backend/API are unaffected by visual changes)

### "User wants to add a field to a database table"

1. `docs/DATABASE.md` — Add column to CREATE TABLE, add index if needed
2. `docs/API.md` — Add field to response objects if exposed via API
3. `docs/FRONTEND.md` — Add field to TypeScript interface
4. `docs/IMPLEMENTATION.md` — Note in Phase 1 (models) if it needs special handling
5. `docs/DATABASE.md` — Update seed data spec if the field needs populated

### "User wants to remove a feature"

1. `docs/PRD.md` — Delete the feature section or move to Out of Scope
2. Remove references from: DATABASE.md, API.md, FRONTEND.md, IMPLEMENTATION.md
3. Delete any related mockup files

---

## Important Conventions

- **Feature numbering**: F1-F16 currently. Always increment (don't reuse deleted numbers).
- **SQL style**: PostgreSQL 16 syntax. Use `gen_random_uuid()` for UUIDs, `TIMESTAMPTZ` for dates.
- **API style**: REST, JSON responses, snake_case field names. Auth via Clerk JWT (header: `Authorization: Bearer <token>`).
- **TypeScript style**: Interfaces (not types), camelCase field names matching the API's snake_case via the `apiFetch` function.
- **Acceptance criteria**: Always use `- [ ]` checkbox format in PRD.md.
- **Priorities**: P0 = must have, P1 = important, P2 = nice to have, Low = optional.

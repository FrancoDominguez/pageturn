# Instructions for the Implementation Agent

## Context

You are picking up the PageTurn project — a library catalogue and management system. All planning, architecture, and design docs have been created. Your job is to implement the entire project from these specs.

**GitHub Repo**: https://github.com/FrancoDominguez/pageturn
**Local Path**: `/Users/francodominguez/valsoft`

---

## Before You Start

### 1. UI Design Selection
The user has been presented with 5 UI design mockups in `mockups/`. They will tell you which one they picked (Option A through E), or they may ask you to iterate on a design.

**When you know the chosen design**:
1. Read `mockups/option-{x}-home.html` and `mockups/option-{x}-detail.html` to extract the design tokens
2. Update `docs/FRONTEND.md` — replace the placeholder design system section with the actual colors, fonts, and styling from the chosen mockup
3. Use these design tokens when building all frontend components

If the user wants to iterate on a design (e.g., "I like Option D but with Option A's font"), create a new mockup HTML combining those elements, let them approve it, then extract the final tokens.

### 2. Manual Setup — COMPLETE
All prerequisites are done. The `.env` file exists at the project root with:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — Clerk publishable key
- `CLERK_SECRET_KEY` — Clerk secret key
- `DATABASE_URL` — Neon pooled connection string (database `neondb` already exists)
- `GCP_PROJECT_ID` — `valsoft-library-demo-488905` (project already created with Cloud Run enabled)

CLIs are all authenticated via OAuth (no tokens needed):
- `neonctl` — OAuth as `franco.dominguez343@gmail.com`
- `vercel` — logged in as `francodominguez`
- `gcloud` — `franco.dominguez343@gmail.com`, project `valsoft-library-demo-488905`
- `kaggle` — API key for `FrancoADominguez` (requires `$HOME/.local/bin` in PATH)

**Important differences from original plan**:
- GCP project is `valsoft-library-demo-488905` (not `pageturn-mcp`) — do NOT create a new project
- Clerk key uses `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (not `CLERK_PUBLISHABLE_KEY`)
- No `VERCEL_TOKEN` or `NEON_API_KEY` — use CLI commands directly (already authenticated)
- Neon database already exists — do NOT create a new project, just run migrations against existing `DATABASE_URL`

---

## Documentation Map

Read these docs in this order before starting:

| Doc | Purpose | Read When |
|-----|---------|-----------|
| `ARCHITECTURE.md` | High-level overview, project structure, tech stack | First — sets the context |
| `docs/IMPLEMENTATION.md` | **Master build guide** — follow this step by step | Your primary reference |
| `docs/DATABASE.md` | Full SQL schema, indexes, triggers, seed specs | When building Phase 1-2 |
| `docs/API.md` | Every REST endpoint with request/response contracts | When building Phase 2 |
| `docs/FRONTEND.md` | Component tree, page specs, React Query hooks, types | When building Phase 4 |
| `docs/MCP.md` | MCP tool specs, auth flow, server pattern | When building Phase 5 |
| `docs/DEPLOYMENT.md` | CLI commands for infra setup and deployment | When deploying |
| `docs/PRD.md` | Product requirements with acceptance criteria | Reference for feature completeness |
| `docs/BUSINESS_SUMMARY.md` | Non-technical overview | Not needed for implementation |

---

## Implementation Order

Follow `docs/IMPLEMENTATION.md` exactly. The phases are:

1. **Phase 0**: Environment setup (git, directories, dataset download)
2. **Phase 1**: Backend foundation (Python env, config, DB models, auth, migrations)
3. **Phase 2**: Core API (all REST endpoints with business logic)
4. **Phase 3**: Seed data (books from CSV, mock users/loans/fines/reviews)
5. **Phase 4**: Frontend (React + TS, all pages and components)
6. **Phase 5**: MCP servers (user + admin)
7. **Phase 6**: Deployment (Vercel + Cloud Run)
8. **Phase 7**: Admin promotion and final verification

**Phases 4 and 5 can be built in parallel after Phase 2.**

---

## Key Implementation Notes

### Backend
- Use SQLAlchemy 2.0 style (`Mapped` annotations, `select()` not `query()`)
- All endpoints follow the patterns in `docs/API.md` — response shapes must match exactly
- Business logic goes in service files (`api/app/services/`), not in routers
- Full-text search uses PostgreSQL `tsvector` + `GIN` index — see `docs/DATABASE.md` for the trigger SQL
- Clerk JWT verification using `python-jose` — JWKS cached for 1 hour
- API key auth for MCP uses SHA-256 hashing — see `docs/API.md` auth section

### Frontend
- Design tokens come from the selected mockup (CSS custom properties)
- Use React Query for ALL server state — no `useState` for API data
- Clerk's `<SignedIn>` / `<SignedOut>` components for auth gating
- Every page has loading skeletons and empty states
- Search is debounced (300ms) with URL search params for shareability

### MCP
- MCP servers are thin wrappers around the REST API
- User context comes from the API key (resolved to user_id)
- No recommendation algorithm — the AI agent does the reasoning using the data tools

### Database
- After creating SQLAlchemy models, run `alembic revision --autogenerate`
- **Then manually add** the SQL functions and triggers to the migration (Alembic can't detect raw SQL)
- See `docs/DATABASE.md` for the exact SQL to add

---

## Verification

After each phase, verify it works:

- **Phase 1**: `alembic upgrade head` succeeds, tables exist in Neon
- **Phase 2**: `uvicorn app.main:app --reload` starts, hit `GET /api/books` returns empty list
- **Phase 3**: `python -m app.seed.run_seed` succeeds, `GET /api/books` returns books
- **Phase 4**: `npm run dev` starts, homepage shows books with covers
- **Phase 5**: Claude Desktop connects and responds to "what books are available?"
- **Phase 6**: Production URLs work end-to-end

---

## Git Workflow

- Commit after each phase is complete
- Use descriptive commit messages: "Phase 1: Backend foundation with DB models and auth"
- Push to `main` after each phase
- The repo is already initialized with remote `origin` at `git@github.com:FrancoDominguez/pageturn.git`

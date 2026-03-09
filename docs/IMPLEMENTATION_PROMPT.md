# PageTurn — One-Shot Implementation Prompt

**Purpose**: Hand this prompt to an AI coding agent (Claude Code, Cursor, etc.) to implement the entire project from the existing specs.

---

## The Prompt

```
You are implementing PageTurn — a full-stack library catalogue and management system with AI agent integration via MCP. All planning docs, architecture, database schema, API spec, frontend spec, and deployment guide are already written. Your job is to build it.

## Project Location
- Repo: /Users/francodominguez/valsoft (git remote: git@github.com:FrancoDominguez/pageturn.git)
- Branch: `main` (docs are on `docs/planning` — merge or cherry-pick as needed)

## Read These First (in order)
1. `AGENT_INSTRUCTIONS.md` — Your instructions, doc map, verification steps
2. `ARCHITECTURE.md` — High-level overview, project structure, tech stack
3. `docs/IMPLEMENTATION.md` — **Master build guide — follow this step by step**

## Reference Docs (read as needed per phase)
- `docs/DATABASE.md` — Full SQL schema, indexes, triggers, seed specs (Phase 1-2)
- `docs/API.md` — Every REST endpoint with request/response contracts (Phase 2)
- `docs/FRONTEND.md` — Component tree, page specs, design tokens, TypeScript types (Phase 4)
- `docs/MCP.md` — MCP tool specs, auth flow, server pattern (Phase 5)
- `docs/DEPLOYMENT.md` — CLI commands for infra setup and deployment (Phase 6)
- `docs/PRD.md` — Product requirements with acceptance criteria (reference for completeness)

## Critical Implementation Notes

### Before starting
1. `MANUAL_SETUP.md` is COMPLETE. `.env` exists with Clerk keys + `DATABASE_URL` + `GCP_PROJECT_ID`. All CLIs authenticated via OAuth. GCP project is `valsoft-library-demo-488905` (reuse it, don't create new). Neon database `neondb` already exists (just run migrations). No `VERCEL_TOKEN` or `NEON_API_KEY` needed — CLIs are logged in. Kaggle CLI needs `export PATH="$HOME/.local/bin:$PATH"`. Clerk key is `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (not `CLERK_PUBLISHABLE_KEY`).
2. The UI design is finalized — use the design tokens from `docs/FRONTEND.md` (Bold Modern theme for users, Notion/Stripe dense style for admin)
3. Mockups exist in `mockups/` for ALL pages (user-facing AND admin). Mockups show the approved layout and visual style. The FRONTEND.md spec has the full behaviors, data fetching, edge cases, modals, and business logic. Use BOTH — mockups for look-and-feel, FRONTEND.md for everything else.

### Known fixes from plan review (apply during implementation)
- Add `SELECT ... FOR UPDATE` to checkout and reservation copy selection queries (prevent race conditions)
- Each API endpoint returns domain-specific keys (`books`, `loans`, etc.) not generic `items` — create per-endpoint response types in TypeScript
- Add `POST /api/admin/loans/{loan_id}/lost` to the loans router (mark loan as lost)
- Add `PUT /api/admin/book-copies/{copy_id}` to the books router (update copy status/condition)
- Create `seed_reservations.py` in Phase 3 (30 mock reservations)
- Add `is_staff_pick` and `staff_pick_note` to admin book creation endpoint
- Add API key expiry check (`expires_at`) to the `get_api_key_user` auth dependency
- Remove the MCP `checkout_book` fallback — POST /api/loans handles auto-reservation in one call
- Add `CRON_SECRET` to environment variables
- Add webhook idempotency (ON CONFLICT handling in Clerk webhook)
- File `routes/ai-assistant.tsx` (not `settings.tsx`)
- Add `get_reading_profile` MCP tool file

### Implementation order
Follow `docs/IMPLEMENTATION.md` exactly:
- Phase 0: Environment setup
- Phase 1: Backend foundation (models, migrations, auth)
- Phase 2: Core API (all endpoints)
- Phase 3: Seed data (books from CSV, mock users/loans/fines/reviews/reservations)
- Phase 4: Frontend (React + TS, all pages)
- Phase 5: MCP servers (user + admin, 22 tools)
- Phase 6: Deployment (Vercel + Cloud Run)
- Phase 7: Admin promotion, verification, README

### After each phase
Verify it works before moving on:
- Phase 1: `alembic upgrade head` succeeds
- Phase 2: `uvicorn app.main:app --reload` starts, `GET /api/books` works
- Phase 3: `python -m app.seed.run_seed` populates data
- Phase 4: `npm run dev` shows homepage with books
- Phase 5: Claude Desktop connects via MCP
- Phase 6: Production URLs work end-to-end

### README
After deployment, write the README following `docs/README_SPEC.md`. Key points:
- Present it as a product, not an assignment
- The MCP integration is the headline feature
- Include the "Why MCP, Not a Chatbot" reasoning: Non-power users use the UI. Power users already have their own AI agents — they don't want a chatbot on the website, they want their existing agents to have access to the system. MCP makes the AI interface composable, not locked-in. A chatbot would be annoying to power users and nearly unusable compared to their own agent setup. This is the same principle for any vertical SaaS: don't build a chatbot on every product, build MCP tools that let any AI agent operate the system.
- Keep it scannable — a hiring manager should get the value in 30 seconds
- Include screenshots of key pages
- Include the Claude Desktop config snippet
- Mention it was built with Claude Code (demonstrates AI-native development)
- This project is for the Agent Builder role at Manos Software (Valsoft). The README should connect the project to the role: "The same pattern — expose domain operations as MCP tools, let the LLM orchestrate — could be applied to any of Valsoft's 30+ portfolio companies."

### Git workflow
- Commit after each phase is complete
- Descriptive commit messages
- Push to `main` after each phase

### Quality bar
- Every page has loading skeletons and empty states
- Every API endpoint handles errors with descriptive messages
- Search is debounced (300ms) with URL params for shareability
- Design tokens are consistent across all components
- Mock data makes every page populated — zero empty states in the demo
- MCP tools return helpful error messages (not just "Error" but "You have $12.50 in outstanding fines. Would you like me to show your fines?")
```

---

## Usage

Copy the prompt above and paste it into a new Claude Code session (or similar AI coding agent). The agent will read the docs and implement the full project.

**Estimated implementation time**: 3-5 focused sessions with AI assistance.

**Prerequisites**: User must complete `MANUAL_SETUP.md` first (~20 minutes of manual account creation for Clerk, Neon, Vercel, GCP, Kaggle).

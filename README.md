# PageTurn

A modern library management system with AI-powered tools for both patrons and administrators.

**[Live Demo](https://frontend-rho-ruby-13.vercel.app)** &nbsp;&middot;&nbsp; React &nbsp;&middot;&nbsp; FastAPI &nbsp;&middot;&nbsp; PostgreSQL &nbsp;&middot;&nbsp; Clerk &nbsp;&middot;&nbsp; MCP

---

PageTurn is a full-stack library catalogue with checkout, reservations, fines, reviews, and a dual-scope MCP server that lets any AI agent operate the system on behalf of users and admins. It demonstrates building AI agent interfaces for vertical market software — the same pattern that scales across portfolio companies.

## Quick Start

```bash
git clone https://github.com/FrancoDominguez/pageturn.git
cd pageturn

# Backend
cd api && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # fill in Clerk + Neon credentials
alembic upgrade head
python -m scripts.seed   # loads 1000+ books from Kaggle
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

## Features at a Glance

| Members | Admins |
|---|---|
| Full-text book search (weighted: title > author > description > genre) | Dashboard with live stats (books, copies, loans, overdue, users, fines) |
| Filter by genre, item type, availability | Book CRUD with full metadata (title, author, ISBN, description, cover, etc.) |
| Sort by relevance, title, rating, publication year | Copy management (add copies, update condition, mark damaged/lost) |
| Book detail with metadata, availability, and community reviews | Staff pick management (toggle + librarian note) |
| One-click checkout (auto-reserves when unavailable) | User management (search, view full profile, edit settings) |
| Loan management with due dates and renewal tracking | Role promotion/demotion (synced to Clerk) |
| Loan renewal (up to 2x, blocked when someone is waiting) | View all active and overdue loans across users |
| Loan history with "Borrow Again" links | Process returns (triggers fine calculation + reservation queue) |
| Reservation waitlist with queue position and 48h pickup window | Mark loans as lost ($30 fee or replacement cost) |
| Fine tracking with daily accrual breakdown by item type | Fine management (view all, filter by status, waive individual fines) |
| Book reviews and ratings (1-5 stars + optional text) | AI admin assistant via MCP (9 admin-only tools) |
| Review nudge for recently returned books | Cron: overdue detection (daily) + reservation expiry (hourly) |
| AI assistant via MCP (13 tools — search, checkout, renew, recommend) | |
| SSO authentication (Google + email via Clerk) | |
| Staff Picks and Top Rated browsing sections | |

## Why MCP, Not a Chatbot

Non-power users use the UI. Power users already have their own AI agents — Claude Desktop, custom setups, IDE integrations. They don't want to interact with a website chatbot. They want their existing agents to have access to the library system.

A website chatbot forces users into a lowest-common-denominator interface. MCP lets every user bring their own agent, their own preferences, their own workflows. The AI interface becomes composable, not locked-in.

This is the same principle that applies to vertical market software: don't build a chatbot on every product. Build MCP tools that let any AI agent operate the system. One integration, every agent.

## AI Integration

PageTurn exposes a dual-scope MCP server — 13 tools for members, 22 for admins — running on Cloud Run as a single container with route-based scope selection.

Users generate API keys from the web app, then point their AI agent at the MCP endpoint. The agent authenticates with the key and gets access to the full tool set for that user's scope. No custom client needed — any MCP-compatible agent works out of the box.

**Claude Desktop configuration:**
```json
{
  "mcpServers": {
    "pageturn": {
      "url": "https://pageturn-mcp-612431506627.us-central1.run.app/user/mcp",
      "headers": {
        "Authorization": "Bearer pt_usr_your_key_here"
      }
    }
  }
}
```

**Example prompts:**
- "What should I read next based on my history?"
- "Check out Dune for me"
- "Show all overdue loans and waive fines under $2"

The recommendation strategy is intentional: MCP provides raw data (reading profile, loan history, reviews, genre preferences), and the LLM does the reasoning. No recommendation algorithm needed — the intelligence is in the agent. This keeps the server stateless and lets users benefit from model improvements without code changes.

**User tools (13):** search books, get book details, checkout, return, renew loan, list loans, loan history, reserve, cancel reservation, list reservations, list fines, reading profile, write review

**Admin tools (+9):** create/update/delete books, manage copies, process returns, manage users, waive fines, view stats, manage staff picks

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React + TypeScript + Vite | Fast builds, type safety |
| Styling | Tailwind CSS | Utility-first, no CSS files |
| Auth | Clerk | SSO + webhooks, zero config |
| Backend | FastAPI (Python) | Async, auto-docs, Pydantic |
| Database | Neon (PostgreSQL) | Serverless, branching, free tier |
| MCP Server | mcp Python SDK | Official protocol implementation |
| Frontend Hosting | Vercel | Git push to deploy |
| Backend Hosting | Vercel (serverless) | Same platform, simple config |
| MCP Hosting | Google Cloud Run | Container with HTTP streaming |

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│   Database   │
│  React + TS  │     │   FastAPI    │     │   Neon PG    │
│   (Vercel)   │     │   (Vercel)   │     │  (Serverless)│
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │                      ▲
                            │                      │
┌──────────────┐     ┌──────┴───────┐              │
│ Claude / AI  │────▶│  MCP Server  │──────────────┘
│   Agent      │     │ (Cloud Run)  │
└──────────────┘     └──────────────┘
                            ▲
                            │
                     ┌──────┴───────┐
                     │    Clerk     │
                     │   (Auth)     │
                     └──────────────┘
```

- **Frontend** — SPA with React Router, TanStack Query for data fetching, Clerk components for auth
- **Backend** — REST API with 30+ endpoints, async SQLAlchemy, Pydantic validation, Clerk JWT verification
- **Database** — PostgreSQL with full-text search (tsvector), GIN indexes, trigger-based search vector updates
- **MCP Server** — Streamable HTTP transport, API key auth, route-based scope selection (/user vs /admin)
- **Clerk** — Webhook sync on user create/update/delete, JWT verification on API requests

## Project Structure

```
pageturn/
├── api/               # FastAPI backend (routers, models, services, auth)
│   ├── app/           # Application code
│   └── alembic/       # Database migrations
├── frontend/          # React + TypeScript SPA
│   └── src/           # Components, routes, hooks, types
├── mcp/               # MCP server (user + admin tools)
│   └── tools/         # Tool implementations by domain
├── scripts/           # Seed data, admin promotion, API key generation
├── data/              # Kaggle book dataset
├── docs/              # PRD, API spec, database spec, deployment guide
└── mockups/           # HTML design mockups (style references)
```

## Built With AI

This project was built using Claude Code as the primary development tool — from planning docs through implementation and deployment. The planning phase produced 15+ specification documents, and the implementation was executed from a one-shot prompt referencing those specs. This demonstrates the "bias toward action" and "zero to prototype quickly" approach the Agent Builder role requires.

## How to Run Locally

**Prerequisites:** Node 20+, Python 3.12+, a Clerk account, a Neon database

1. **Clone and set up environment variables:**
   ```bash
   git clone https://github.com/FrancoDominguez/pageturn.git
   cd pageturn
   cp .env.example .env
   # Fill in: CLERK_SECRET_KEY, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
   #          CLERK_WEBHOOK_SECRET, DATABASE_URL
   ```

2. **Backend:**
   ```bash
   cd api
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   cd .. && python -m scripts.seed
   uvicorn app.main:app --reload --app-dir api
   ```

3. **Frontend:**
   ```bash
   cd frontend
   npm install
   echo "VITE_API_URL=http://localhost:8000" > .env
   npm run dev
   ```

4. **MCP Server (optional):**
   ```bash
   cd mcp
   pip install -r requirements.txt
   python main.py
   ```

## How to Deploy

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for full instructions. Three deployment targets:

- **Frontend** → Vercel (static SPA)
- **Backend** → Vercel (serverless Python)
- **MCP Server** → Google Cloud Run (containerized)

## License

MIT

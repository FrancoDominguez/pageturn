# PageTurn — README Specification

**Purpose**: Instructions for the implementation agent to write a README that maximizes hiring impact.

---

## Context

This project is a submission for an **Agent Builder** position at Manos Software Group (part of Valsoft Corporation). The role involves building AI agent systems for vertical market software companies. The README needs to:

1. Satisfy the assignment requirements (working product, source code, brief explanation)
2. Demonstrate the exact skills they're hiring for
3. Be impressive without being verbose — respect the reader's time

## Assignment Requirements (Must Cover)

From the Valsoft challenge:
- Working product using any language/framework/AI tools
- Source code with a brief README explaining how to run it
- Bonus: deploy + provide live URL
- Bonus: auth with SSO and user roles
- Bonus: AI features
- Bonus: extra features showing creativity

## README Structure

### Header
- Project name: **PageTurn**
- One-line tagline: "A modern library management system with AI-powered tools for both patrons and administrators"
- Live demo link (Vercel URL)
- Short badges row (React, FastAPI, PostgreSQL, Clerk, MCP)

### The Hook (2-3 sentences max)
- What it is
- What makes it different (the MCP AI integration)
- Why it matters for the role ("demonstrates building AI agent interfaces for vertical market software")

### Quick Start
- Prerequisites (Node 20+, Python 3.12+)
- Clone, install, configure `.env`, seed, run
- Keep it to ~10 lines of shell commands

### Features at a Glance
Use this two-column table in the README. It shows the full scope at a glance.

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
| "Currently Reading" section on homepage | |
| Staff Picks and Top Rated browsing sections | |

### Why MCP, Not a Chatbot (include this reasoning)
- **The core argument**: Non-power users use the UI. Power users already have their own AI agents (Claude Desktop, custom setups). They don't want to interact with a website chatbot — they want their existing agents to have access to the library system.
- A website chatbot forces users into a lowest-common-denominator interface. MCP lets every user bring their own agent, their own preferences, their own workflows.
- This is the same principle that applies to Valsoft's portfolio companies: don't build a chatbot on every product. Build MCP tools that let any AI agent operate the system. The AI interface becomes composable, not locked-in.
- Frame this as a deliberate architectural decision, not a shortcut.

### AI Integration Deep-Dive (this is the money section)
- Explain the MCP architecture in 4-5 sentences
- Show the Claude Desktop config snippet
- List 3 example prompts ("What should I read next based on my history?", "Check out Dune for me", "Show all overdue loans")
- Explain WHY this matters: the AI agent becomes a natural interface for library operations — exactly what Manos wants to build for their portfolio companies
- Mention the dual-scope design (user vs admin MCP) and the 22 tools
- The recommendation strategy: MCP provides raw data (reading profile, history, reviews), the LLM does the reasoning. No recommendation algorithm needed — the intelligence is in the agent.

### Tech Stack
- Simple table: Layer | Technology | Why
- Keep "Why" to 5 words max per row

### Architecture
- The ASCII deployment diagram from DEPLOYMENT.md
- One sentence per component

### Screenshots
- 3-4 key screenshots: homepage, book detail, loans page, admin dashboard
- Caption each with what it shows

### Project Structure
- Abbreviated tree (just top-level dirs with one-line descriptions)

### Built With AI
- Brief note that this was built using Claude Code as the primary development tool
- This demonstrates the "bias toward action" and "zero to prototype quickly" values from the job description

### How to Run Locally
- Detailed steps (expand on Quick Start)
- Include: env setup, database migration, seed data, start dev servers

### How to Deploy
- Link to DEPLOYMENT.md for full instructions
- Quick summary of the 3 deployment targets

### License
- MIT

## Tone Guidelines

- **Direct and confident.** No hedging, no "this is just a demo." Present it as a real product.
- **Technical but accessible.** A CTO should be able to scan it; a developer should want to dig in.
- **Show, don't tell.** Screenshots and code snippets over paragraphs of text.
- **No fluff.** Every sentence earns its place. If it doesn't add value, cut it.
- **Let the work speak.** The project is impressive — the README just needs to present it clearly.

## Anti-Patterns to Avoid

- Don't list every single feature exhaustively
- Don't include a wall of text about the tech stack decisions
- Don't add "Future Improvements" section (this implies it's incomplete)
- Don't use emojis or excessive formatting
- Don't apologize for anything
- Don't mention it's a "test" or "assignment" — present it as a product you chose to build

## Key Message to Convey

"I took a simple library CRUD assignment and turned it into a production-grade AI-integrated platform — the same kind of vertical market AI product this role exists to build. The MCP integration turns a traditional web app into something an AI agent can operate, demonstrating exactly how I'd add AI capabilities to any of your 30+ portfolio companies."

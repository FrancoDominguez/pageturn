# AI-Driven User Acceptance Testing (UAT) for PageTurn

## Research Document -- March 2026

---

## Table of Contents

1. [Playwright MCP Approach](#1-playwright-mcp-approach)
2. [Traditional Playwright Testing](#2-traditional-playwright-testing)
3. [Other Browser Agent Approaches](#3-other-browser-agent-approaches)
4. [Recommended Approach for PageTurn](#4-recommended-approach-for-pageturn)
5. [Implementation Sketch](#5-implementation-sketch)

---

## 1. Playwright MCP Approach

### What It Is

The Playwright MCP server (`@playwright/mcp`, currently v0.0.68) is a Model Context Protocol server from Microsoft that exposes Playwright's browser automation capabilities as MCP tools. This allows an AI agent -- such as Claude via Claude Code or Claude Desktop -- to navigate a live web application, interact with elements, and verify behavior using structured accessibility snapshots rather than pixel-based vision.

The key insight: the MCP server represents the page as an **accessibility tree** (a structured text representation of the DOM), not as screenshots. This means the AI agent can interact deterministically with elements by their role, name, and state -- no vision model required.

### Available Tools

The `@playwright/mcp` server exposes approximately 25 tools organized into categories:

**Navigation:** `browser_navigate`, `browser_navigate_back`, `browser_navigate_forward`, `browser_tab_new`, `browser_tab_select`, `browser_tab_close`, `browser_tab_list`

**Element Interaction:** `browser_click`, `browser_type`, `browser_hover`, `browser_select_option`, `browser_drag`, `browser_press_key`, `browser_file_upload`

**Page Analysis:** `browser_snapshot` (accessibility tree), `browser_take_screenshot`, `browser_console_messages`, `browser_network_requests`

**Utility:** `browser_wait_for`, `browser_handle_dialog`, `browser_close`, `browser_resize`, `browser_pdf_save`

**Code Generation:** `browser_generate_playwright_test`, `start_codegen_session`, `end_codegen_session`

For 80% of UAT work, you use: `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_select_option`, `browser_press_key`, and `browser_wait_for`.

### How UAT Would Work

1. You give Claude a PRD acceptance criterion (e.g., "Search bar on homepage accepts free-text queries; results match against title, author, description, genre")
2. Claude uses `browser_navigate` to open the app
3. Claude uses `browser_snapshot` to read the page structure
4. Claude uses `browser_type` to enter "science fiction" in the search bar
5. Claude uses `browser_click` to submit the search
6. Claude uses `browser_snapshot` again to read the results
7. Claude reasons about whether the results satisfy the acceptance criterion
8. Claude reports pass/fail with evidence

### Setup

**Install and configure the MCP server in Claude Code:**

```bash
claude mcp add playwright -- npx @playwright/mcp@latest
```

**Or in `claude_desktop_config.json`:**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "timeout": 30000
    }
  }
}
```

The server auto-installs Chromium on first use. No additional browser binaries needed.

**For test code generation, add the `--codegen` flag:**

```bash
claude mcp add playwright -- npx @playwright/mcp@latest --codegen
```

This makes Claude output reusable Playwright TypeScript alongside its actions.

### Pros

- **Natural language test specs.** You describe acceptance criteria in English; the AI agent figures out how to verify them. No selectors, no test scripts to write or maintain.
- **Exploratory testing.** Claude can explore the app, find edge cases, and test paths you didn't explicitly specify. "Try to check out a book when you have $15 in outstanding fines and see what happens."
- **Adaptive to UI changes.** Because the AI reads the accessibility tree and reasons about intent, a button moving from the sidebar to the header doesn't break the "test." The AI finds it by its role/label.
- **Generates Playwright code.** With `--codegen`, every MCP interaction produces reusable TypeScript that can be committed as a traditional Playwright test. You get AI-driven exploration AND a permanent test suite.
- **Low barrier to entry.** No test framework setup, no page object models, no fixture files. Just a prompt.
- **Already available in this project.** The Playwright MCP server is already configured as a tool in the development environment (visible in the available deferred tools list).

### Cons

- **Non-deterministic.** The AI may take different paths each run. A "test" that passed yesterday might interact differently today -- not because the app changed, but because the AI reasoned differently. This makes it unsuitable as a CI gate without additional structure.
- **Slow.** Each tool call involves an LLM inference round-trip. A single "test" that a Playwright script runs in 2 seconds might take 30-60 seconds via MCP because of the back-and-forth between Claude and the browser.
- **Expensive.** Every MCP interaction consumes API tokens. Running a full UAT suite of 50+ scenarios could cost $5-20+ per run depending on complexity.
- **Authentication complexity.** Clerk SSO flows involve redirects, iframes, and third-party domains that are tricky for an AI agent to navigate reliably. The agent might get stuck on the Clerk sign-in modal, especially with Google OAuth.
- **No native CI integration.** You can't easily run "Claude + Playwright MCP" in a GitHub Actions pipeline today without custom orchestration. It's fundamentally an interactive tool.
- **Flaky assertions.** The AI's judgment on "does this look correct?" is probabilistic. It might miss subtle bugs (wrong color, off-by-one in pagination) or flag false positives.

---

## 2. Traditional Playwright Testing

### What It Is

Standard Playwright (`@playwright/test`) is Microsoft's open-source end-to-end testing framework. Tests are written in TypeScript, executed headlessly in CI, and produce deterministic pass/fail results. This is the industry standard for web application E2E testing.

### How It Works for PageTurn

```typescript
// tests/search.spec.ts
import { test, expect } from '@playwright/test';

test('F1: Search bar accepts free-text queries and returns relevant results', async ({ page }) => {
  await page.goto('/');

  // Type in search bar
  await page.getByPlaceholder('Search books...').fill('science fiction');
  await page.getByRole('button', { name: 'Search' }).click();

  // Verify results appear
  await expect(page.getByTestId('search-results')).toBeVisible();
  const results = page.getByTestId('book-card');
  await expect(results).toHaveCount({ min: 1 });

  // Verify result relevance (title or genre contains search terms)
  const firstResult = results.first();
  const title = await firstResult.getByTestId('book-title').textContent();
  const genre = await firstResult.getByTestId('book-genre').textContent();
  expect(
    title?.toLowerCase().includes('science fiction') ||
    genre?.toLowerCase().includes('science fiction')
  ).toBeTruthy();
});
```

### Clerk Authentication in Tests

Clerk officially supports Playwright via the `@clerk/testing` package. This is critical for PageTurn.

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';
import { clerk } from '@clerk/testing/playwright';

setup('authenticate as user', async ({ page }) => {
  // setupClerkTestingToken bypasses bot detection
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.TEST_USER_EMAIL!,
      password: process.env.TEST_USER_PASSWORD!,
    },
  });

  // Save signed-in state for reuse
  await page.context().storageState({ path: 'tests/.auth/user.json' });
});

setup('authenticate as admin', async ({ page }) => {
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.TEST_ADMIN_EMAIL!,
      password: process.env.TEST_ADMIN_PASSWORD!,
    },
  });

  await page.context().storageState({ path: 'tests/.auth/admin.json' });
});
```

**Requirements:**
- `@clerk/testing` package (npm)
- Test users with **password authentication** enabled in Clerk (not just Google SSO)
- Clerk development instance keys as environment variables: `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`
- The `setupClerkTestingToken()` or `clerk.signIn()` call bypasses Clerk's bot detection, which would otherwise block Playwright

### Can Tests Be Auto-Generated from PRDs?

**Yes, and this is now a practical workflow.** There are two approaches:

**Approach A: Claude Code + Playwright MCP codegen**

1. Feed Claude the PRD acceptance criteria
2. Claude uses Playwright MCP with `--codegen` to explore the live app
3. Each interaction generates TypeScript test code
4. Claude uses `start_codegen_session` / `end_codegen_session` to produce complete test files
5. You review and commit the generated tests

This is sometimes called "vibe testing" -- the AI explores and generates. The output is standard Playwright TypeScript you can run in CI forever after.

**Approach B: Claude Code generates tests directly from PRD**

1. Give Claude the PRD, the frontend component code, and the data-testid conventions
2. Claude writes Playwright test files directly (no browser needed for generation)
3. Run the tests; Claude fixes any failures

Approach B is faster but produces tests that might not match reality. Approach A is slower but tests are validated against the live app during generation.

**Playwright also ships three built-in AI agents** (as of late 2025):
- **Planner Agent:** Explores the app and produces a Markdown test plan
- **Generator Agent:** Transforms the plan into Playwright test files using real selectors
- **Healer Agent:** Automatically fixes broken locators when the UI changes

### Pros

- **Deterministic.** Same test, same result. Reliable CI gates.
- **Fast.** Full suite of 50+ tests runs in under 2 minutes (parallel execution).
- **Free to run.** No API token costs. Runs on GitHub Actions free tier.
- **Clerk has first-party support.** `@clerk/testing` solves the auth problem cleanly.
- **Industry standard.** Every team member knows Playwright. Extensive documentation, community, and tooling.
- **Trace viewer and reports.** Built-in HTML reports, trace files for debugging, video recording, screenshot comparison.

### Cons

- **Maintenance burden.** When the UI changes, tests break and need updating. Page object models help but don't eliminate this.
- **Selector brittleness.** Tests depend on CSS selectors, data-testid attributes, or ARIA roles being stable. If someone removes a `data-testid`, the test breaks.
- **Doesn't test "intent."** A Playwright test checks that a specific element exists with specific text. It doesn't understand whether the user experience is actually good.
- **Writing tests takes time.** Even with AI generation, someone needs to review, tune, and maintain the test suite.

---

## 3. Other Browser Agent Approaches

### 3.1 Stagehand (by Browserbase)

**What:** An open-source browser automation SDK built for AI agents. Provides three atomic primitives (`act`, `extract`, `observe`) plus a high-level `Agent` mode.

**Repository:** [github.com/browserbase/stagehand](https://github.com/browserbase/stagehand) (TypeScript), [github.com/browserbase/stagehand-python](https://github.com/browserbase/stagehand-python) (Python)

**Current Version:** v3 (44% faster than v2, uses CDP directly)

**How it works:**
```typescript
import { Stagehand } from '@browserbase/stagehand';

const stagehand = new Stagehand({ env: 'LOCAL' }); // or 'BROWSERBASE' for cloud
await stagehand.init();
await stagehand.page.goto('https://pageturn.app');

// Natural language actions
await stagehand.act('Search for science fiction books');
await stagehand.act('Click on the first book result');

// Structured data extraction
const bookDetails = await stagehand.extract({
  instruction: 'Extract the book title, author, and availability status',
  schema: z.object({
    title: z.string(),
    author: z.string(),
    available: z.boolean(),
  }),
});
```

**Relevance to PageTurn:**
- Can run locally (free) or on Browserbase cloud (paid, but provides session recording and parallel execution)
- Works with any LLM backend (OpenAI, Anthropic, etc.)
- The `extract` primitive with Zod schemas is excellent for structured assertions ("extract all book titles from the search results and verify they contain 'science fiction'")
- Python SDK available if you want to integrate with the FastAPI backend tests
- No native Clerk integration -- you'd need to handle auth separately

**Verdict:** Strong for building custom AI-driven test harnesses. More programmatic control than Playwright MCP, but requires writing a test runner. Good if you want AI flexibility with code structure.

### 3.2 BrowserBase (Cloud Infrastructure)

**What:** Cloud infrastructure for running headless browsers at scale. Not a testing framework itself, but the hosting layer for Stagehand and other browser agents.

**URL:** [browserbase.com](https://www.browserbase.com/)

**Relevance:** If you want to run Stagehand or Playwright in the cloud (e.g., for parallel test execution without local resources), Browserbase provides session management, recording, and scaling. Pricing starts at free tier for limited usage. Partnered with Google DeepMind for browser agent training.

**Verdict:** Nice-to-have infrastructure, not essential for PageTurn's scale (~1,000 books, ~50 users). Local Playwright is sufficient.

### 3.3 testRigor

**What:** Commercial SaaS platform for AI-powered test automation. Tests are written in plain English.

**URL:** [testrigor.com](https://testrigor.com/)

**How it works:** You write test cases like:
```
login as "testuser@example.com" with password "test123"
click "Search"
type "science fiction" into search bar
check that page contains "Science Fiction" at least 3 times
click on first "Book Card"
check that "Available" is displayed
```

**Relevance:** Can auto-generate tests from app descriptions and specifications. Handles auth flows, visual validation, email testing. Adapts to UI changes automatically.

**Verdict:** Interesting for teams without test engineering capacity. Commercial product with per-seat pricing. Overkill for a project that already has developer tooling. The plain-English syntax doesn't provide meaningful advantages over Claude + Playwright MCP for a technical team.

### 3.4 Momentic

**What:** AI-powered test automation platform that records user behavior and transforms it into automated test flows.

**URL:** [momentic.ai](https://momentic.ai/)

**Relevance:** Records real user sessions and converts them to tests. AI re-generates broken steps automatically. Good for teams that want zero-code test creation.

**Verdict:** Similar to testRigor. Commercial SaaS, not open-source. Better suited for product/QA teams than developer-led testing.

### 3.5 Vercel's Agent Browser

**What:** An experimental browser automation CLI from Vercel Labs for AI agents.

**Repository:** [github.com/vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)

**Relevance:** Since PageTurn deploys on Vercel, this could integrate nicely. However, it's experimental and not production-ready.

**Verdict:** Watch this space, but don't build on it today.

### 3.6 Playwright Skill for Claude Code

**What:** A community-built Claude Code "skill" that provides structured Playwright automation capabilities.

**Repository:** [github.com/lackeyjb/playwright-skill](https://github.com/lackeyjb/playwright-skill)

**Relevance:** Designed specifically for Claude Code to write and execute Playwright tests autonomously. One blog post documented generating 82 E2E tests for an e-commerce app using this skill. The skill provides Claude with context on Playwright best practices and patterns.

**Verdict:** Lightweight, free, and directly relevant. Worth evaluating alongside the official Playwright MCP.

---

## 4. Recommended Approach for PageTurn

### Strategy: Hybrid -- Traditional Playwright as Foundation, AI-Assisted Generation, MCP for Exploration

Given PageTurn's tech stack (React 18, Clerk auth, FastAPI, seeded mock data), the recommended approach is a **three-layer testing strategy**:

### Layer 1: Traditional Playwright Test Suite (CI Gate)

**This is the backbone.** A deterministic, fast, reliable Playwright test suite that runs on every PR.

**Why:**
- Clerk has first-party Playwright support (`@clerk/testing`) -- this is the single biggest factor. Clerk auth is the hardest part of automated testing for this app, and it's already solved for traditional Playwright.
- Tests run in CI (GitHub Actions) in under 2 minutes.
- Free to execute. No API costs.
- Produces HTML reports, traces, and screenshots for debugging.
- The seeded database (50 users, 1,000 books, 500 loans) provides predictable test data.

**Coverage targets (mapped to PRD features):**

| Feature | Test Count | Auth Required |
|---------|-----------|---------------|
| F1: Book Search & Browse | 8 | No |
| F2: Book Detail Page | 6 | No |
| F3: User Authentication | 4 | Mixed |
| F4: Book Checkout | 7 | User |
| F5: Loan Management | 6 | User |
| F6: Reservation System | 8 | User |
| F7: Reviews & Ratings | 5 | User |
| F8: Fines & Dues | 4 | User |
| F9: Admin Book Management | 6 | Admin |
| F10: Admin User Management | 4 | Admin |
| F11: Admin Dashboard | 3 | Admin |
| F12: AI Assistant Page | 3 | User |
| **Total** | **~64** | |

### Layer 2: AI-Assisted Test Generation (Developer Workflow)

**Use Claude Code + Playwright MCP with `--codegen` to generate the initial test suite from PRD acceptance criteria.**

The workflow:
1. Feed Claude the PRD feature spec (e.g., F4: Book Checkout acceptance criteria)
2. Claude navigates the live app via MCP, interacting with each acceptance criterion
3. With `--codegen`, each interaction generates TypeScript
4. Claude produces a complete `checkout.spec.ts` file
5. Developer reviews, adjusts selectors to use `data-testid` where appropriate, and commits
6. From then on, the test runs deterministically in CI

This dramatically reduces the time to write the initial 64 tests. Estimate: 2-4 hours with AI generation vs. 2-3 days writing manually.

### Layer 3: MCP-Driven Exploratory UAT (Pre-Release)

**Use Playwright MCP interactively before major releases to do exploratory testing that goes beyond the scripted suite.**

Example prompts for pre-release UAT:
- "Navigate to PageTurn as a new user. Try to discover and check out a book. Report any UX friction."
- "Log in as an admin. Try adding a book with missing required fields. Verify error handling."
- "Try checking out a book, then find that book in your loans, try to renew it twice, then try a third time and verify the renewal is blocked."
- "Check if the fine calculation on the fines page matches the expected rate of $0.25/day for a book that's 14 days overdue."

This is not a CI gate -- it's a human-in-the-loop QA session where Claude acts as a tireless manual tester.

### Handling Clerk Auth Across All Layers

**This is the most important technical consideration.** Here's how auth works in each layer:

| Layer | Auth Method |
|-------|------------|
| Traditional Playwright | `@clerk/testing` package: `clerk.signIn()` with test user credentials. Bypasses bot detection. Saves auth state for reuse across tests. Requires password-based test users in Clerk dev instance. |
| AI Test Generation | Same as above -- Claude generates tests that use `@clerk/testing`. |
| MCP Exploratory | **Harder.** The MCP agent would need to navigate Clerk's sign-in UI. Options: (a) Use Clerk's `<SignIn>` component with email+password, not Google OAuth. (b) Pre-set auth cookies/localStorage before MCP session. (c) Use a custom test route that sets auth state. |

**Critical setup requirement:** Create dedicated test users in Clerk with **email+password** authentication (not just Google SSO). These accounts are used by both the Playwright test suite and MCP exploratory testing.

### MCP Endpoint Testing

The PageTurn MCP servers (user and admin) should be tested at the **API level**, not through browser automation:

```typescript
// tests/mcp/user-tools.spec.ts
import { test, expect } from '@playwright/test';

test('MCP: search_books returns relevant results', async ({ request }) => {
  const response = await request.post('http://localhost:8080/user', {
    headers: { 'Authorization': `Bearer ${process.env.TEST_MCP_API_KEY}` },
    data: {
      method: 'tools/call',
      params: { name: 'search_books', arguments: { query: 'science fiction' } }
    }
  });

  const body = await response.json();
  expect(body.content).toBeDefined();
  expect(body.content[0].text).toContain('science fiction');
});
```

Playwright's `request` API is perfect for this -- same test framework, same CI pipeline, no browser needed.

### Why Not Pure AI Testing?

Several reasons specific to PageTurn:

1. **Clerk auth.** The `@clerk/testing` package only works with traditional Playwright. There's no MCP equivalent.
2. **Seeded data assumptions.** Tests need predictable data ("book X should be available"). AI agents can adapt, but deterministic assertions on known data are more reliable.
3. **CI integration.** A GitHub Actions pipeline that runs `npx playwright test` is trivial. A pipeline that spins up Claude to drive a browser is not.
4. **Cost.** 64 tests x ~$0.10-0.50 per MCP-driven test = $6-32 per CI run. Traditional Playwright: $0.
5. **Speed.** 64 Playwright tests: ~90 seconds. 64 MCP-driven tests: ~30-60 minutes.

---

## 5. Implementation Sketch

### Phase 1: Infrastructure Setup (Day 1)

**1a. Install Playwright and Clerk testing packages:**

```bash
cd frontend/
npm install -D @playwright/test @clerk/testing
npx playwright install chromium
```

**1b. Configure Playwright (`playwright.config.ts`):**

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined, // Clerk has issues with too many parallel workers
  reporter: [['html'], ['json', { outputFile: 'test-results.json' }]],

  use: {
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    // Auth setup runs first
    { name: 'auth-setup', testMatch: /auth\.setup\.ts/, teardown: 'cleanup' },
    { name: 'cleanup', testMatch: /auth\.teardown\.ts/ },

    // Public tests (no auth needed)
    {
      name: 'public',
      testMatch: /public\/.*\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },

    // User tests (authenticated)
    {
      name: 'user',
      testMatch: /user\/.*\.spec\.ts/,
      dependencies: ['auth-setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'tests/.auth/user.json',
      },
    },

    // Admin tests (admin authenticated)
    {
      name: 'admin',
      testMatch: /admin\/.*\.spec\.ts/,
      dependencies: ['auth-setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'tests/.auth/admin.json',
      },
    },

    // MCP API tests (no browser)
    {
      name: 'mcp',
      testMatch: /mcp\/.*\.spec\.ts/,
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

**1c. Create test users in Clerk dev instance:**

- `testuser@pageturn-test.example.com` (role: user, password auth enabled)
- `testadmin@pageturn-test.example.com` (role: admin, password auth enabled)
- Seed these users in the database with known loan/fine/review data

**1d. Set up environment variables (`.env.test`):**

```bash
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
TEST_USER_EMAIL=testuser@pageturn-test.example.com
TEST_USER_PASSWORD=TestPassword123!
TEST_ADMIN_EMAIL=testadmin@pageturn-test.example.com
TEST_ADMIN_PASSWORD=AdminPassword123!
TEST_MCP_API_KEY=pt_usr_test...
TEST_MCP_ADMIN_KEY=pt_adm_test...
```

### Phase 2: Auth Setup & Core Tests (Day 2)

**2a. Auth setup file:**

```typescript
// tests/auth.setup.ts
import { test as setup } from '@playwright/test';
import { clerk } from '@clerk/testing/playwright';

setup('authenticate as regular user', async ({ page }) => {
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.TEST_USER_EMAIL!,
      password: process.env.TEST_USER_PASSWORD!,
    },
  });
  await page.context().storageState({ path: 'tests/.auth/user.json' });
});

setup('authenticate as admin', async ({ page }) => {
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.TEST_ADMIN_EMAIL!,
      password: process.env.TEST_ADMIN_PASSWORD!,
    },
  });
  await page.context().storageState({ path: 'tests/.auth/admin.json' });
});
```

**2b. Write first test files (or generate them with Claude + MCP):**

```
tests/
  auth.setup.ts
  public/
    search.spec.ts         # F1 acceptance criteria
    book-detail.spec.ts    # F2 acceptance criteria
  user/
    checkout.spec.ts       # F4 acceptance criteria
    loans.spec.ts          # F5 acceptance criteria
    reservations.spec.ts   # F6 acceptance criteria
    reviews.spec.ts        # F7 acceptance criteria
    fines.spec.ts          # F8 acceptance criteria
    ai-assistant.spec.ts   # F12 acceptance criteria
  admin/
    books.spec.ts          # F9 acceptance criteria
    users.spec.ts          # F10 acceptance criteria
    dashboard.spec.ts      # F11 acceptance criteria
  mcp/
    user-tools.spec.ts     # F13 MCP tool tests
    admin-tools.spec.ts    # F14 MCP tool tests
```

### Phase 3: AI-Assisted Test Generation (Day 2-3)

Use Claude Code with Playwright MCP to generate the initial test files:

```
Prompt: "I need to create Playwright tests for the PageTurn library app.
Here are the acceptance criteria for F4 (Book Checkout):
[paste acceptance criteria from PRD]

The app is running at http://localhost:5173. Auth is already set up
via @clerk/testing (storageState files exist). The test user has the
following seeded data: 3 active loans, $5 in fines, and one book
reserved.

Navigate the app and generate a complete checkout.spec.ts file that
verifies each acceptance criterion. Use data-testid selectors where
possible, fall back to getByRole/getByText."
```

Claude will use the MCP to explore the live app and produce test code. Review and commit.

### Phase 4: CI Pipeline (Day 3)

**GitHub Actions workflow (`.github/workflows/e2e.yml`):**

```yaml
name: E2E Tests
on:
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Install Playwright browsers
        working-directory: frontend
        run: npx playwright install chromium --with-deps

      - name: Run Playwright tests
        working-directory: frontend
        run: npx playwright test
        env:
          CLERK_PUBLISHABLE_KEY: ${{ secrets.CLERK_PUBLISHABLE_KEY }}
          CLERK_SECRET_KEY: ${{ secrets.CLERK_SECRET_KEY }}
          TEST_USER_EMAIL: ${{ secrets.TEST_USER_EMAIL }}
          TEST_USER_PASSWORD: ${{ secrets.TEST_USER_PASSWORD }}
          TEST_ADMIN_EMAIL: ${{ secrets.TEST_ADMIN_EMAIL }}
          TEST_ADMIN_PASSWORD: ${{ secrets.TEST_ADMIN_PASSWORD }}
          TEST_BASE_URL: ${{ secrets.TEST_BASE_URL }}
          TEST_MCP_API_KEY: ${{ secrets.TEST_MCP_API_KEY }}
          TEST_MCP_ADMIN_KEY: ${{ secrets.TEST_MCP_ADMIN_KEY }}

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

### Phase 5: Ongoing MCP Exploratory Testing (Ongoing)

Before each release, run exploratory UAT sessions using Claude + Playwright MCP:

```
Prompt: "PageTurn is about to release. The app is live at
https://staging.pageturn.app. Run through the complete user journey:

1. Browse the homepage (verify genre accordions, staff picks, search)
2. Sign in as testuser@pageturn-test.example.com
3. Search for a book, view details, check it out
4. Go to My Loans, verify the new loan appears
5. Try to renew it
6. Go to Loan History, verify past loans exist
7. Leave a review on a book from history
8. Check the Fines page
9. Visit the AI Assistant page

Report any bugs, UX issues, or acceptance criteria violations you find.
Reference the PRD feature IDs (F1-F16) in your findings."
```

### Cost & Time Estimates

| Activity | One-Time Cost | Per-Run Cost | Duration |
|----------|--------------|-------------|----------|
| Playwright setup + config | 2-4 hours | - | - |
| AI-generated test suite (64 tests) | 4-6 hours (review) | - | - |
| CI pipeline per PR | - | $0 (GitHub Actions) | ~2 min |
| MCP exploratory UAT session | - | ~$2-5 (Claude API) | ~15-30 min |
| Test maintenance per month | - | - | ~2-4 hours |

---

## Summary

| Approach | Best For | PageTurn Use |
|----------|----------|-------------|
| **Traditional Playwright** | CI gates, regression, auth flows | Primary -- ~64 tests, runs on every PR |
| **Playwright MCP (codegen)** | Generating the initial test suite from PRDs | One-time generation, then commit as traditional tests |
| **Playwright MCP (interactive)** | Exploratory UAT, pre-release validation | Pre-release sessions with Claude |
| **Stagehand/Browserbase** | Custom AI agent test harnesses | Not needed at PageTurn's scale |
| **testRigor/Momentic** | Non-technical QA teams | Not a fit for this developer-led project |

The recommended path: **Use Claude + Playwright MCP to generate the initial Playwright test suite from PRD acceptance criteria, then run those tests deterministically in CI on every PR. Use MCP exploratory sessions for pre-release UAT.**

---

## Sources

- [Microsoft Playwright MCP -- GitHub](https://github.com/microsoft/playwright-mcp)
- [@playwright/mcp -- npm](https://www.npmjs.com/package/@playwright/mcp)
- [Testing with Playwright -- Clerk Docs](https://clerk.com/docs/guides/development/testing/playwright/overview)
- [Test Authenticated Flows -- Clerk + Playwright](https://clerk.com/docs/guides/development/testing/playwright/test-authenticated-flows)
- [Clerk Test Helpers for Playwright](https://clerk.com/docs/guides/development/testing/playwright/test-helpers)
- [@clerk/testing -- npm](https://www.npmjs.com/package/@clerk/testing)
- [Stagehand v3 -- Browserbase](https://www.browserbase.com/blog/stagehand-v3)
- [Stagehand GitHub](https://github.com/browserbase/stagehand)
- [Write Automated Tests with Claude Code Using Playwright Agents](https://shipyard.build/blog/playwright-agents-claude-code/)
- [Playwright Skill for Claude Code](https://github.com/lackeyjb/playwright-skill)
- [From Acceptance Criteria to Playwright Tests with MCP](https://dev.to/yerac/from-acceptance-criteria-to-playwright-tests-with-mcp-4ka6)
- [How to Use Claude Code to Write Playwright Tests with Playwright MCP](https://getdecipher.com/blog/how-to-use-claude-code-to-write-playwright-tests-(with-playwright-mcp))
- [Generate E2E Tests with AI and Playwright -- Checkly](https://www.checklyhq.com/blog/generate-end-to-end-tests-with-ai-and-playwright/)
- [The Complete Playwright End-to-End Story -- Microsoft](https://developer.microsoft.com/blog/the-complete-playwright-end-to-end-story-tools-ai-and-real-world-workflows)
- [testRigor](https://testrigor.com/)
- [Momentic](https://momentic.ai/)
- [Vercel Agent Browser](https://github.com/vercel-labs/agent-browser)
- [Browserbase](https://www.browserbase.com/)

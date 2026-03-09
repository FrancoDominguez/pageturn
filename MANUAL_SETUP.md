# PageTurn — Manual Setup Checklist

> **STATUS: COMPLETE** — All steps below have been completed as of 2026-03-08.
> The `.env` file exists at the project root with all required credentials.

---

## Step 1: Clerk (Authentication) — DONE

- Application created: "PageTurn" (test mode)
- Sign-in methods: Google + Email enabled
- Keys saved to `.env`:
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_c29s...`
  - `CLERK_SECRET_KEY=sk_test_zbp6...`
- Webhooks: **not yet configured** — happens after backend deploy

---

## Step 2: Neon Database — DONE

- Account: `franco.dominguez343@gmail.com`
- Database `neondb` exists on Neon serverless
- Connection string saved to `.env` as `DATABASE_URL`
- `neonctl` v2.21.2 installed and authenticated via OAuth (no API key needed)

---

## Step 3: Vercel — DONE

- `vercel` CLI installed and logged in as `francodominguez`
- Authenticated via OAuth (no token needed — CLI is already logged in)
- No `VERCEL_TOKEN` required; use `vercel` CLI commands directly

---

## Step 4: Google Cloud Platform — DONE

- Account: `franco.dominguez343@gmail.com` (personal, NOT deck.co)
- Project: `valsoft-library-demo-488905` (already created with billing)
- Cloud Run API: enabled
- Existing Cloud Run service: `valsoft-library-api` in `us-central1`
- `gcloud` CLI installed and authenticated
- GCP project ID saved to `.env` as `GCP_PROJECT_ID`
- **No need to create a new project** — reuse `valsoft-library-demo-488905`

---

## Step 5: Kaggle — DONE

- Account: `FrancoADominguez`
- `kaggle` CLI v2.0.0 installed (via pipx, requires `$HOME/.local/bin` in PATH)
- API credentials at `~/.kaggle/kaggle.json`
- Verified working: can list datasets

---

## `.env` File (created at project root)

```bash
# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=              # Set after backend deploy

# Database (Neon — pooled connection)
DATABASE_URL=postgresql://neondb_owner:...@ep-icy-brook-aheeliru-pooler...

# Google Cloud
GCP_PROJECT_ID=valsoft-library-demo-488905

# App
FRONTEND_URL=http://localhost:5173
API_URL=http://localhost:8000
MCP_URL=http://localhost:8080
CRON_SECRET=                       # Generate at build time
```

---

## CLI Authentication Summary

All CLIs are authenticated via OAuth/browser login. No tokens or API keys needed in `.env` for CLI usage.

| CLI | Version | Auth Method |
|-----|---------|-------------|
| `neonctl` | 2.21.2 | OAuth (browser) |
| `vercel` | latest | OAuth (logged in as `francodominguez`) |
| `gcloud` | latest | OAuth (`franco.dominguez343@gmail.com`) |
| `kaggle` | 2.0.0 | API key (`~/.kaggle/kaggle.json`) |
| `node` | 25.8.0 | N/A |

---

## Post-Implementation Manual Step

After the backend is deployed, configure the Clerk webhook:

1. The agent deploys the backend **first** (without `CLERK_WEBHOOK_SECRET`)
2. Get backend URL from the agent (e.g., `https://pageturn-api.vercel.app`)
3. In Clerk Dashboard → **Webhooks** → **Add Endpoint**
4. URL: `https://YOUR_BACKEND_URL/api/webhooks/clerk`
5. Select events: `user.created`, `user.updated`, `user.deleted`
6. Click **Create**
7. Copy the **Signing Secret** (starts with `whsec_`)
8. Tell the agent → it sets `CLERK_WEBHOOK_SECRET` and redeploys

**This is the only remaining manual step.**

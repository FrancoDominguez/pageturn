# PageTurn — Deployment & Infrastructure

---

## Architecture Diagram

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

---

## Prerequisites Setup — COMPLETED

> All CLIs are installed and authenticated as of 2026-03-08. See `MANUAL_SETUP.md` for full status.

| CLI | Version | Auth | Account |
|-----|---------|------|---------|
| `node` | 25.8.0 | N/A | N/A |
| `neonctl` | 2.21.2 | OAuth | `franco.dominguez343@gmail.com` |
| `vercel` | latest | OAuth | `francodominguez` |
| `gcloud` | latest | OAuth | `franco.dominguez343@gmail.com` |
| `kaggle` | 2.0.0 | API key | `FrancoADominguez` |

### Clerk — DONE
- Application "PageTurn" created (test mode)
- Keys in `.env`: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`
- Webhooks: configure after backend deploy

---

## Infrastructure Provisioning — COMPLETED

### Neon Database — DONE
- Database `neondb` already exists
- Pooled connection string in `.env` as `DATABASE_URL`
- Endpoint: `ep-icy-brook-aheeliru-pooler.c-3.us-east-1.aws.neon.tech`
- No need to create a new project

### GCP Project — DONE
- Project: `valsoft-library-demo-488905` (already created with billing)
- Cloud Run API: enabled
- Cloud Build API: enabled
- Artifact Registry API: enabled
- Active account: `franco.dominguez343@gmail.com`

**Note**: The GCP project ID is `valsoft-library-demo-488905` (not `pageturn-mcp` as originally planned). Update all `gcloud` commands to use this project ID. It's already set as the active project in `gcloud config`.

### Download Book Dataset

```bash
# kaggle requires $HOME/.local/bin in PATH
export PATH="$HOME/.local/bin:$PATH"
kaggle datasets download -d dylanjcastillo/7k-books-with-metadata \
  --unzip \
  -p ./data/
```

---

## Environment Variables

### `.env` (Root) — ALREADY CREATED

```bash
# === Clerk ===
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=              # Set after backend deploy

# === Database (Neon — pooled) ===
DATABASE_URL=postgresql://neondb_owner:...@ep-icy-brook-aheeliru-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require

# === Google Cloud ===
GCP_PROJECT_ID=valsoft-library-demo-488905

# === App ===
FRONTEND_URL=http://localhost:5173
API_URL=http://localhost:8000
MCP_URL=http://localhost:8080
CRON_SECRET=                       # Generate at build time
```

> **Note**: No `VERCEL_TOKEN` or `NEON_API_KEY` needed — CLIs are authenticated via OAuth.
> The Clerk key name uses `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (Next.js convention also works with Vite via alias).

### Frontend Environment (`.env.local`)

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
VITE_API_URL=http://localhost:8000/api
```

### Backend Environment

```bash
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=sk_test_xxxxx
CLERK_WEBHOOK_SECRET=whsec_xxxxx
FRONTEND_URL=http://localhost:5173
CRON_SECRET=<random-secret-for-vercel-cron>
```

### MCP Server Environment

```bash
DATABASE_URL=postgresql://...
API_BASE_URL=https://api.pageturn.app
```

---

## Deployment Steps

### Deploy Backend to Vercel

```bash
cd api/

# First deployment — creates the project
vercel --prod --token $VERCEL_TOKEN --yes

# Set environment variables
echo "$DATABASE_URL" | vercel env add DATABASE_URL production --token $VERCEL_TOKEN
echo "$CLERK_SECRET_KEY" | vercel env add CLERK_SECRET_KEY production --token $VERCEL_TOKEN
echo "$CLERK_WEBHOOK_SECRET" | vercel env add CLERK_WEBHOOK_SECRET production --token $VERCEL_TOKEN
echo "$FRONTEND_URL" | vercel env add FRONTEND_URL production --token $VERCEL_TOKEN

# Redeploy with env vars
vercel --prod --token $VERCEL_TOKEN --yes
```

**Backend `vercel.json`**:
```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

**Backend `requirements.txt`**:
```
fastapi>=0.109.0
uvicorn>=0.27.0
sqlalchemy[asyncio]>=2.0.25
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
alembic>=1.13.0
pydantic>=2.6.0
pydantic-settings>=2.1.0
httpx>=0.27.0
python-jose[cryptography]>=3.3.0
svix>=1.21.0
faker>=22.0.0
```

### Deploy Frontend to Vercel

```bash
cd frontend/

# First deployment
vercel --prod --token $VERCEL_TOKEN --yes

# Set environment variables
echo "$CLERK_PUBLISHABLE_KEY" | vercel env add VITE_CLERK_PUBLISHABLE_KEY production --token $VERCEL_TOKEN

# Get backend URL from previous deployment
BACKEND_URL=$(vercel ls --token $VERCEL_TOKEN | grep api | awk '{print $2}')
echo "https://$BACKEND_URL/api" | vercel env add VITE_API_URL production --token $VERCEL_TOKEN

# Redeploy
vercel --prod --token $VERCEL_TOKEN --yes
```

**Frontend `vercel.json`**:
```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/api/:path*", "destination": "${VITE_API_URL}/:path*" }
  ]
}
```

### Deploy MCP to Cloud Run

```bash
cd mcp/

# Build container image
gcloud builds submit \
  --tag gcr.io/valsoft-library-demo-488905/pageturn-mcp:latest

# Deploy
gcloud run deploy pageturn-mcp \
  --image gcr.io/valsoft-library-demo-488905/pageturn-mcp:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$DATABASE_URL,API_BASE_URL=https://YOUR_BACKEND.vercel.app" \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300

# Get the URL
MCP_URL=$(gcloud run services describe pageturn-mcp \
  --region us-central1 \
  --format "value(status.url)")

echo "MCP Server URL: $MCP_URL"
```

### Configure Clerk Webhook

**Note: Two-deploy sequence required.** The backend must be deployed first to get a URL, then the webhook is created in Clerk to get the signing secret, then the backend must be redeployed with that secret. This is an inherent circular dependency — you cannot get `CLERK_WEBHOOK_SECRET` until the webhook endpoint exists, but you need the backend URL to create the webhook.

**Step-by-step**:

1. Deploy the backend **first** (even without `CLERK_WEBHOOK_SECRET` — the webhook endpoint will exist but fail signature verification)
2. Get backend URL: `https://your-api.vercel.app`
3. In Clerk Dashboard → Webhooks → Add Endpoint
4. URL: `https://your-api.vercel.app/api/webhooks/clerk`
5. Events: `user.created`, `user.updated`, `user.deleted`
6. Copy the signing secret → set as `CLERK_WEBHOOK_SECRET` env var in Vercel
7. **Redeploy** the backend with the new env var

```bash
echo "whsec_xxxxx" | vercel env add CLERK_WEBHOOK_SECRET production --token $VERCEL_TOKEN
vercel --prod --token $VERCEL_TOKEN --yes  # Second deploy with webhook secret
```

---

## Database Migrations

```bash
cd api/

# Run migrations against Neon
DATABASE_URL="$DATABASE_URL" alembic upgrade head
```

For the initial migration, after defining all SQLAlchemy models:
```bash
alembic revision --autogenerate -m "initial_schema"
```

Then manually add to the migration:
- `books_search_vector_update()` function
- `update_book_rating()` function
- `update_updated_at()` function
- All triggers
- The `calculate_fine()` function

---

## Seed Data

```bash
cd api/

# Run the complete seed
DATABASE_URL="$DATABASE_URL" python -m app.seed.run_seed

# Or individual seeders
python -m app.seed.seed_books      # Load ~1,000 books from CSV
python -m app.seed.seed_users      # Generate 50 mock users
python -m app.seed.seed_loans      # Generate 500 mock loans
python -m app.seed.seed_fines      # Generate fines for late loans
python -m app.seed.seed_reviews    # Generate 200 mock reviews
```

The seed script path to the Kaggle CSV: `data/7k-books-with-metadata.csv` (from the `dylanjcastillo/7k-books-with-metadata` Kaggle dataset).

---

## Local Development

### Backend

```bash
cd api/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env with DATABASE_URL, CLERK_SECRET_KEY, etc.

# Run migrations
alembic upgrade head

# Seed data
python -m app.seed.run_seed

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend/
npm install

# Create .env.local with VITE_CLERK_PUBLISHABLE_KEY, VITE_API_URL

npm run dev  # Starts on localhost:5173
```

### MCP Server (local testing)

```bash
cd mcp/
pip install -r requirements.txt

# Run locally
uvicorn server:app --port 8080
```

Test with Claude Desktop by updating `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "pageturn": {
      "url": "http://localhost:8080/user",
      "headers": {
        "Authorization": "Bearer pt_usr_xxxxx"
      }
    }
  }
}
```

---

## Post-Deployment Checklist

- [ ] Backend health check: `curl https://api.pageturn.app/api/books?limit=1`
- [ ] Frontend loads: open `https://pageturn.app`
- [ ] Clerk sign-in works: click Sign In, complete flow
- [ ] Webhook fires: check Clerk dashboard → Webhooks → Logs
- [ ] Search works: type a query, verify results
- [ ] Book detail loads: click a book card
- [ ] Checkout works: sign in, check out a book
- [ ] Admin panel: sign in as admin, verify stats load
- [ ] MCP user: configure Claude Desktop, ask "what books are available?"
- [ ] MCP admin: configure with admin key, ask "show overdue books"

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

## Prerequisites Setup (CLI Commands)

### 1. Install CLIs

```bash
# Node.js (if not installed)
brew install node

# Vercel CLI
npm i -g vercel

# Neon CLI
brew install neonctl
# Alternative: npm i -g neonctl

# Google Cloud CLI
brew install --cask google-cloud-sdk

# Kaggle CLI
pip install kaggle

# Python (if not 3.12+)
brew install python@3.12
```

### 2. Authenticate CLIs

```bash
# Neon (using API key from neon.tech dashboard)
export NEON_API_KEY="your_neon_api_key_here"

# Vercel (using token from vercel.com/account/tokens)
export VERCEL_TOKEN="your_vercel_token_here"

# Google Cloud
gcloud auth login
# When prompted, open browser and authenticate

# Kaggle (place the kaggle.json from kaggle.com/settings)
mkdir -p ~/.kaggle
cp ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### 3. Clerk Setup (Manual — Browser Required)

1. Go to https://dashboard.clerk.com
2. Click "Create application"
3. Name: "PageTurn"
4. Enable sign-in methods: Google, Email
5. Go to "API Keys" in the sidebar
6. Copy:
   - `CLERK_PUBLISHABLE_KEY` (starts with `pk_`)
   - `CLERK_SECRET_KEY` (starts with `sk_`)
7. Go to "Webhooks" → will be configured after backend deployment

---

## Infrastructure Provisioning (Automated)

### Create Neon Database

```bash
# Create project
NEON_PROJECT_ID=$(neonctl projects create \
  --name pageturn \
  --region-id aws-us-east-2 \
  --output json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

echo "Neon Project ID: $NEON_PROJECT_ID"

# Get connection string (pooled for serverless)
DATABASE_URL=$(neonctl connection-string \
  --project-id $NEON_PROJECT_ID \
  --pooled \
  --output json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['connection_string'])")

echo "DATABASE_URL: $DATABASE_URL"
```

### Create GCP Project + Enable Cloud Run

```bash
GCP_PROJECT_ID="pageturn-mcp"

# Create project
gcloud projects create $GCP_PROJECT_ID --name="PageTurn MCP"

# Link billing (use your billing account ID from console.cloud.google.com/billing)
gcloud billing projects link $GCP_PROJECT_ID \
  --billing-account=YOUR_BILLING_ACCOUNT_ID

# Set as active project
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Download Book Dataset

```bash
kaggle datasets download -d dylanjcastillo/7k-books-with-metadata \
  --unzip \
  -p ./data/
```

---

## Environment Variables

### `.env.example` (Root)

```bash
# === Clerk ===
CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
CLERK_WEBHOOK_SECRET=whsec_xxxxx

# === Database ===
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# === Vercel ===
VERCEL_TOKEN=xxxxx

# === Google Cloud ===
GCP_PROJECT_ID=pageturn-mcp

# === Neon ===
NEON_API_KEY=xxxxx

# === App ===
FRONTEND_URL=http://localhost:5173
API_URL=http://localhost:8000
MCP_URL=http://localhost:8080
CRON_SECRET=xxxxx
```

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
  --tag gcr.io/$GCP_PROJECT_ID/pageturn-mcp:latest

# Deploy
gcloud run deploy pageturn-mcp \
  --image gcr.io/$GCP_PROJECT_ID/pageturn-mcp:latest \
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

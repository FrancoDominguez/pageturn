# PageTurn — Manual Setup Checklist

Everything the implementation agent can't do for you. Complete these steps before starting implementation. Total time: ~20 minutes.

---

## Step 1: Clerk (Authentication) — ~5 min

Clerk has no CLI. This must be done in the browser.

1. Go to https://dashboard.clerk.com and sign up / sign in
2. Click **"Create application"**
3. Name: **"PageTurn"**
4. Under **Sign-in methods**, enable:
   - **Google** (toggle on)
   - **Email** (toggle on — this enables email + password and magic links)
5. Click **Create**
6. Go to **"API Keys"** in the left sidebar
7. Copy these two values and save them:
   - `CLERK_PUBLISHABLE_KEY` — starts with `pk_test_` or `pk_live_`
   - `CLERK_SECRET_KEY` — starts with `sk_test_` or `sk_live_`
8. **Don't configure webhooks yet** — that happens after the backend is deployed

**Save**: `CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`

---

## Step 2: Neon Database — ~3 min

1. Go to https://neon.tech and sign up / sign in
2. In the Neon Console, go to **Settings → API Keys**
3. Click **"Generate API Key"**
4. Name: "PageTurn CLI"
5. Copy the API key

**Save**: `NEON_API_KEY`

> The agent will use `neonctl` CLI to create the database project and get the connection string automatically.

---

## Step 3: Vercel — ~3 min

1. Go to https://vercel.com and sign up / sign in (use GitHub for easiest setup)
2. Go to **Settings → Tokens** (https://vercel.com/account/tokens)
3. Click **"Create Token"**
4. Name: "PageTurn CLI"
5. Scope: Full Account
6. Copy the token

**Save**: `VERCEL_TOKEN`

> The agent will use `vercel` CLI to deploy and configure everything.

---

## Step 4: Google Cloud Platform (for MCP server) — ~5 min

1. Go to https://console.cloud.google.com
2. Sign up / sign in with your Google account
3. Go to **Billing** (https://console.cloud.google.com/billing)
4. If you don't have a billing account, click **"Create Account"**
   - Name: "Personal"
   - Add a payment method (credit/debit card)
   - Note: Cloud Run free tier covers 2M requests/month — you likely won't be charged
5. Copy the **Billing Account ID** (format: `XXXXXX-XXXXXX-XXXXXX`, visible on the billing overview page)
6. Install the gcloud CLI if not already installed:
   ```bash
   brew install --cask google-cloud-sdk
   ```
7. Authenticate:
   ```bash
   gcloud auth login
   ```
   (This opens a browser window — sign in with your Google account)

**Save**: `GCP_BILLING_ACCOUNT_ID`

---

## Step 5: Kaggle (for book data) — ~2 min

1. Go to https://www.kaggle.com and sign up / sign in
2. Go to **Settings** (https://www.kaggle.com/settings)
3. Scroll to **API** section
4. Click **"Create New API Token"**
5. This downloads a `kaggle.json` file
6. Move it to the right place:
   ```bash
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

**No values to save** — the file is all the agent needs.

---

## Summary: Values to Provide

Once you complete the steps above, create a `.env` file in the project root with these values:

```bash
# Clerk (from Step 1)
CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx

# Neon (from Step 2)
NEON_API_KEY=xxxxx

# Vercel (from Step 3)
VERCEL_TOKEN=xxxxx

# GCP (from Step 4)
GCP_BILLING_ACCOUNT_ID=XXXXXX-XXXXXX-XXXXXX
```

The implementation agent reads from this `.env` and handles the rest:
- Creates the Neon database and gets the connection string
- Deploys to Vercel and sets all env vars
- Creates the GCP project, enables Cloud Run, deploys MCP
- Downloads the Kaggle dataset
- Runs migrations and seeds the database

---

## Post-Implementation Manual Step

After the backend is deployed, you need to configure the Clerk webhook. **This requires a two-deploy sequence** because of a circular dependency: the backend URL is needed to create the webhook, but the webhook signing secret is needed by the backend.

1. The agent deploys the backend **first** (without `CLERK_WEBHOOK_SECRET` — the endpoint will exist but reject webhooks)
2. Get the backend URL from the agent (e.g., `https://pageturn-api.vercel.app`)
3. In Clerk Dashboard → **Webhooks** → **Add Endpoint**
4. URL: `https://YOUR_BACKEND_URL/api/webhooks/clerk`
5. Select events: `user.created`, `user.updated`, `user.deleted`
6. Click **Create**
7. Copy the **Signing Secret** (starts with `whsec_`)
8. Tell the agent the signing secret so it can add it to Vercel env vars
9. The agent **redeploys** the backend with the webhook secret

**This is the only post-deployment manual step.** After the second deploy, webhooks will work and user sync will be live.

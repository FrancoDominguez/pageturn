# PageTurn — 2-Week Hosting Cost Estimate

**Verdict: $0–$10 total. Well under $100.**

---

## Cost Breakdown

| Service | Role | Free Tier | Expected Usage | 2-Week Cost |
|---------|------|-----------|----------------|-------------|
| **Vercel** | Frontend + Backend | 100 GB bandwidth, 150K invocations/mo | ~7K invocations, ~1 GB bandwidth | **$0** (Hobby) or **$10** (if Pro) |
| **Neon** | PostgreSQL database | 0.5 GB storage, 100 CU-hours/mo | ~55 MB storage, ~2 CU-hours | **$0** |
| **Cloud Run** | MCP server | 180K vCPU-sec, 2M requests/mo (always free) | ~200 requests, ~400 vCPU-sec | **$0** |
| **Clerk** | Authentication | 50,000 MRUs/mo | 5–10 users | **$0** |
| **Domain** | URL | Vercel provides `.vercel.app` subdomain | Free subdomain | **$0** |

### Total

| Scenario | Cost |
|----------|------|
| All free tiers | **$0.00** |
| Existing Vercel Pro subscription | **~$10.00** (prorated) |

---

## Key Notes

- **Cloud Run Always Free Tier is permanent** — it is NOT part of the GCP $300 trial credits. Even with exhausted trial credits, the always-free allocation applies. Just need a billing account on file.
- **Neon scales to zero** when idle — no compute charges when nobody's using the app.
- **Cloud Run `min-instances` must be 0** — otherwise it consumes vCPU-seconds continuously.
- **Vercel Hobby tier's 10-second function timeout** is fine for all API endpoints. The seed script must run locally, not on Vercel.
- **Clerk's free tier is 50,000 MRUs** — absurdly generous for a demo with 5–10 users.

## Risk Factors

- If bot traffic hits the site: Vercel bandwidth could spike, but 100 GB free is a huge buffer
- If Cloud Run container is misconfigured with `min-instances > 0`: continuous billing (~$5/day)
- None of these are likely for a 2-week demo period

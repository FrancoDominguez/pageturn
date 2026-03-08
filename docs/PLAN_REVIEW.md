# PageTurn — Plan Review Findings

Review conducted by specialist architecture agent. All 11 project documents reviewed.

---

## Critical Fixes (must fix before implementation)

1. **Race conditions on checkout/reservation** — Add `SELECT ... FOR UPDATE` to checkout and reservation service functions to prevent double-booking
2. **`PaginatedResponse<T>` mismatch** — Frontend uses generic `items` key but API uses domain-specific keys (`books`, `loans`, etc.). Need per-endpoint response types.

## Major Fixes (fix during implementation)

3. `POST /api/admin/loans/{loan_id}/lost` missing from IMPLEMENTATION.md Step 2.3
4. `PUT /api/admin/book-copies/{copy_id}` missing from IMPLEMENTATION.md
5. `seed_reservations.py` missing from Phase 3
6. `is_staff_pick` and `staff_pick_note` not explicitly in admin book creation API spec
7. API key expiry check (`expires_at`) missing from `get_api_key_user` dependency
8. `Fine` TypeScript type has fields (`daily_rate`, `days_overdue`, `book_author`, `book_cover_url`) not in API response
9. MCP `checkout_book` fallback note is wrong — API handles auto-reservation in single call

## Minor Fixes

10. `CRON_SECRET` missing from DEPLOYMENT.md env vars
11. `settings.tsx` should be `ai-assistant.tsx` in IMPLEMENTATION.md
12. `GET /api/loans/{loan_id}` missing from IMPLEMENTATION.md
13. Webhook needs idempotency (ON CONFLICT handling)
14. `DELETE /api/admin/users/{user_id}` discrepancy between ARCHITECTURE.md and API.md
15. `mcp/tools/reading_profile.py` missing from Step 5.3
16. Orphaned loan references when books deleted
17. `plainto_tsquery` doesn't support prefix search ("sci" won't match "science fiction")

## Consistency Confirmed

- Fine rates consistent across all docs
- Loan periods consistent
- Max renewals = 2 consistent
- Checkout blocked at >= $10.00 consistent
- Reservation 48h window consistent
- All 22 MCP tools correctly map to API endpoints

## Risk Areas

- Reservation queue management (concurrent operations)
- Checkout endpoint complexity (6 preconditions)
- MCP SDK evolving — pin version
- Neon cold starts may exceed 500ms NFR
- FastAPI on Vercel serverless (connection pooling issues)

## Impressiveness Assessment

**Verdict: Strong portfolio project for the target role.** MCP integration is genuinely differentiated. Documentation is staff-engineer caliber. The key risk is execution speed — the plan must ship cleanly.

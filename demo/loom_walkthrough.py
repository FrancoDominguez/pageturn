"""
PageTurn — Loom Walkthrough Recorder
=====================================

Drives a headed browser through a smooth, human-like demo of every feature.
You log in manually, press Enter, and the script takes over for Scenes 1-6.
You handle Scene 7 (MCP/AI) yourself afterward.

Usage:
  pip install playwright && playwright install chromium
  python scripts/loom_walkthrough.py                   # all scenes
  python scripts/loom_walkthrough.py --scenes 1 6      # specific scenes
  python scripts/loom_walkthrough.py --local            # use localhost:5173

Recording:
  - Playwright saves a .webm to ./recordings/ automatically
  - For better quality: run Loom/OBS over the headed browser window
  - A blue cursor dot is injected so clicks are visible in recordings
  - Move your real cursor to the screen edge before pressing Enter

Scenes:
  1. Homepage Browse & Search
  2. Book Detail & Checkout
  3. Reservations
  4. Loan History & Reviews
  5. Fines Dashboard
  6. Admin Panel (dashboard, books, users, fines)
"""

import argparse
import asyncio
import os
import random
from playwright.async_api import async_playwright, Page, Locator

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — tweak these to taste
# ═══════════════════════════════════════════════════════════════════════════════

PROD_URL = "https://frontend-rho-ruby-13.vercel.app"
LOCAL_URL = "http://localhost:5173"
VIEWPORT = {"width": 1440, "height": 900}
RECORDING_DIR = "./recordings"

# Pacing (seconds) — slower = more dramatic, faster = tighter video
SHORT = 0.6
MED = 1.2
LONG = 2.0
SCENE_GAP = 2.5
TYPE_DELAY = 65  # ms between keystrokes


# ═══════════════════════════════════════════════════════════════════════════════
# INJECTED CURSOR — visible blue dot that tracks mouse + pulses on click
# ═══════════════════════════════════════════════════════════════════════════════

CURSOR_INIT_SCRIPT = """
(() => {
  function inject() {
    if (document.getElementById('pw-cursor')) return;
    const c = document.createElement('div');
    c.id = 'pw-cursor';
    c.style.cssText = `
      width:20px;height:20px;
      background:rgba(59,130,246,.45);
      border:2px solid rgba(59,130,246,.85);
      border-radius:50%;
      position:fixed;pointer-events:none;
      z-index:2147483647;
      transition:left .06s linear,top .06s linear,transform .12s ease;
      transform:translate(-50%,-50%);
      box-shadow:0 0 12px rgba(59,130,246,.25);
      left:-40px;top:-40px;
    `;
    document.body.appendChild(c);
    document.addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px';});
    document.addEventListener('mousedown',()=>{c.style.transform='translate(-50%,-50%) scale(.65)';c.style.background='rgba(59,130,246,.75)';});
    document.addEventListener('mouseup',()=>{c.style.transform='translate(-50%,-50%) scale(1)';c.style.background='rgba(59,130,246,.45)';});
  }
  if(document.body){inject();}else{document.addEventListener('DOMContentLoaded',inject);}
})()
"""


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def move_to(page: Page, target, offset_x=0, offset_y=0):
    """Smooth cursor glide to the center of a locator or CSS selector."""
    loc = page.locator(target).first if isinstance(target, str) else target
    try:
        await loc.scroll_into_view_if_needed(timeout=3000)
    except Exception:
        pass
    box = await loc.bounding_box()
    if not box:
        return None
    x = box["x"] + box["width"] / 2 + offset_x
    y = box["y"] + box["height"] / 2 + offset_y
    await page.mouse.move(x, y, steps=30)
    return box


async def click(page: Page, target, before=0.25, after=MED):
    """Glide to target, pause, click, pause."""
    loc = page.locator(target).first if isinstance(target, str) else target
    box = await move_to(page, loc)
    if not box:
        return False
    await asyncio.sleep(before)
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2
    await page.mouse.click(x, y)
    await asyncio.sleep(after)
    return True


async def scroll(page: Page, dy: int, duration=1.2):
    """Smooth pixel scroll over duration seconds."""
    steps = 24
    for i in range(steps):
        await page.evaluate(f"window.scrollBy(0,{dy / steps})")
        await asyncio.sleep(duration / steps)


async def type_text(page: Page, target, text: str):
    """Click into a field and type with human cadence."""
    loc = page.locator(target).first if isinstance(target, str) else target
    await click(page, loc, after=0.3)
    await loc.fill("")
    await loc.type(text, delay=TYPE_DELAY)


async def wait_idle(page: Page, t=MED):
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    await asyncio.sleep(t)


async def goto(page: Page, path: str, base: str = ""):
    """Navigate and wait for network idle."""
    url = (base or PROD_URL) + path
    await page.goto(url, wait_until="networkidle", timeout=15000)
    await asyncio.sleep(SHORT)


async def visible(loc: Locator, timeout=2000) -> bool:
    """Quick check if a locator is visible."""
    try:
        await loc.wait_for(state="visible", timeout=timeout)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE 1 — Homepage Browse & Search
# ═══════════════════════════════════════════════════════════════════════════════

async def scene_1(page: Page, base: str):
    print("  Scene 1: Homepage Browse & Search")
    await goto(page, "/", base)
    await asyncio.sleep(LONG)

    # --- Currently Reading section (if logged in with active loans) ---
    cr = page.locator("text=Currently Reading").first
    if await visible(cr, 2000):
        await move_to(page, cr)
        await asyncio.sleep(MED)
        await scroll(page, 300, 1.5)
        await asyncio.sleep(SHORT)

    # --- Hero staff pick ---
    hero_btn = page.locator("a:has-text('Check Out'), button:has-text('Check Out')").first
    if await visible(hero_btn, 2000):
        await move_to(page, hero_btn)
        await asyncio.sleep(MED)

    # --- Scroll through genre accordion sections ---
    await scroll(page, 600, 2.5)
    await asyncio.sleep(MED)
    await scroll(page, 600, 2.5)
    await asyncio.sleep(MED)

    # --- Collapse a section, then reopen (shows accordion) ---
    accordion_btn = page.locator("section.border-b button").nth(2)
    if await visible(accordion_btn, 1500):
        await click(page, accordion_btn, after=SHORT)
        await asyncio.sleep(SHORT)
        await click(page, accordion_btn, after=MED)

    # --- Scroll back up to search ---
    await page.evaluate("window.scrollTo({top:0,behavior:'smooth'})")
    await asyncio.sleep(1.0)

    # --- Type search query ---
    search = page.locator('input[placeholder*="Search"]').first
    await type_text(page, search, "science fiction")
    await asyncio.sleep(SHORT)
    await page.keyboard.press("Enter")
    await wait_idle(page, LONG)

    # --- Browse results ---
    await scroll(page, 350, 1.5)
    await asyncio.sleep(MED)

    # --- Click first book card → detail page ---
    card = page.locator('a[href^="/books/"]').first
    if await visible(card):
        await click(page, card, after=LONG)
        await wait_idle(page, MED)

    # --- Scroll through book detail (metadata, reviews) ---
    await scroll(page, 500, 2.0)
    await asyncio.sleep(LONG)

    print("  ✓ Scene 1 done")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE 2 — Book Checkout
# ═══════════════════════════════════════════════════════════════════════════════

async def scene_2(page: Page, base: str):
    print("  Scene 2: Book Checkout")

    # Search for available books
    await goto(page, "/?q=fiction&sort=title_asc", base)
    await wait_idle(page, MED)

    # Find a card with available copies
    cards = page.locator('a[href^="/books/"]')
    count = await cards.count()
    clicked = False
    for i in range(min(count, 12)):
        text = await cards.nth(i).inner_text()
        if "available" in text.lower() and "0 of" not in text.lower():
            await click(page, cards.nth(i), after=MED)
            clicked = True
            break
    if not clicked and count > 0:
        await click(page, cards.first, after=MED)

    await wait_idle(page, SHORT)

    # Click "Check Out"
    co_btn = page.get_by_role("button", name="Check Out")
    if await visible(co_btn, 3000):
        await click(page, co_btn, after=LONG)
        await wait_idle(page, LONG)

        # Show success banner
        await asyncio.sleep(MED)

        # Navigate to loans
        loans_link = page.locator("a:has-text('View My Loans')").first
        if await visible(loans_link, 2000):
            await click(page, loans_link, after=LONG)
        else:
            await goto(page, "/loans", base)
    else:
        # Book might already be checked out — just go to loans
        await goto(page, "/loans", base)

    await wait_idle(page, MED)
    await scroll(page, 300, 1.5)
    await asyncio.sleep(LONG)

    print("  ✓ Scene 2 done")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE 3 — Reservations & Renewal Blocking
# ═══════════════════════════════════════════════════════════════════════════════

async def scene_3(page: Page, base: str):
    print("  Scene 3: Reservations")

    # Search for highest-rated books (likely checked out)
    await goto(page, "/?q=&sort=rating_desc", base)
    await wait_idle(page, MED)

    # Look for a book showing "0 of" copies
    cards = page.locator('a[href^="/books/"]')
    count = await cards.count()
    clicked = False
    for i in range(min(count, 20)):
        text = await cards.nth(i).inner_text()
        if "0 of" in text.lower():
            await click(page, cards.nth(i), after=MED)
            clicked = True
            break
    if not clicked and count > 2:
        # Just pick the 3rd book and hope it's checked out
        await click(page, cards.nth(2), after=MED)

    await wait_idle(page, SHORT)

    # Click "Reserve" if available
    reserve_btn = page.get_by_role("button", name="Reserve")
    if await visible(reserve_btn, 3000):
        await click(page, reserve_btn, after=LONG)
        await asyncio.sleep(LONG)  # show confirmation banner

    # Go to loans page to show reservations section
    await goto(page, "/loans", base)
    await wait_idle(page, MED)

    # Show any ready-reservation alert
    alert = page.locator("text=Reservation ready").first
    if await visible(alert, 2000):
        await move_to(page, alert)
        await asyncio.sleep(LONG)

    # Scroll to reservations table
    res_heading = page.locator("text=Reservations").first
    if await visible(res_heading, 2000):
        await move_to(page, res_heading)
        await asyncio.sleep(SHORT)
        await scroll(page, 200, 1.0)
        await asyncio.sleep(LONG)

    # Show renewal blocking message if any
    blocked = page.locator("text=Cannot renew").first
    if await visible(blocked, 1500):
        await move_to(page, blocked)
        await asyncio.sleep(LONG)

    print("  ✓ Scene 3 done")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE 4 — Loan History & Reviews
# ═══════════════════════════════════════════════════════════════════════════════

async def scene_4(page: Page, base: str):
    print("  Scene 4: History & Reviews")

    # Navigate via sub-nav
    await goto(page, "/history", base)
    await wait_idle(page, MED)

    # Show review nudge banner if present
    nudge = page.locator("text=How was").first
    if await visible(nudge, 2000):
        await move_to(page, nudge)
        await asyncio.sleep(MED)

    # Scroll through month-grouped history
    await scroll(page, 400, 2.0)
    await asyncio.sleep(MED)

    # Find a "Write Review" link
    write_review = page.locator("a:has-text('Write Review')").first
    if await visible(write_review, 2000):
        await click(page, write_review, after=LONG)
        await wait_idle(page, SHORT)

        # Scroll to reviews section on book detail page
        reviews_h = page.locator("h2:has-text('Reviews')").first
        if await visible(reviews_h, 3000):
            await move_to(page, reviews_h)
            await scroll(page, 150, 0.8)
            await asyncio.sleep(SHORT)

        # Click 4th star (aria-label="4 stars")
        star4 = page.locator('button[aria-label="4 stars"]').first
        if await visible(star4, 2000):
            await click(page, star4, after=SHORT)

        # Type review
        textarea = page.locator("textarea").first
        if await visible(textarea, 2000):
            await type_text(
                page, textarea,
                "A fascinating read that kept me engaged from start to finish. "
                "The world-building is exceptional and the characters feel truly alive."
            )
            await asyncio.sleep(MED)

        # Submit
        submit = page.locator("button:has-text('Submit Review'), button:has-text('Submit')").first
        if await visible(submit, 2000):
            await click(page, submit, after=LONG)
            await asyncio.sleep(LONG)

        # Scroll to show the review appeared
        await scroll(page, 300, 1.5)
        await asyncio.sleep(LONG)
    else:
        # No write-review link — just show the history page
        await scroll(page, 400, 2.0)
        await asyncio.sleep(LONG)

    print("  ✓ Scene 4 done")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE 5 — Fines Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

async def scene_5(page: Page, base: str):
    print("  Scene 5: Fines Dashboard")

    await goto(page, "/fines", base)
    await wait_idle(page, MED)

    # Outstanding balance card
    balance = page.locator("text=Outstanding Balance").first
    if await visible(balance, 2000):
        await move_to(page, balance)
        await asyncio.sleep(LONG)

    # Checkout-blocked warning?
    blocked = page.locator("text=Checkout blocked").first
    if await visible(blocked, 1500):
        await move_to(page, blocked)
        await asyncio.sleep(MED)

    # Scroll through fines table
    await scroll(page, 350, 1.5)
    await asyncio.sleep(MED)

    # Hover over a fine row
    rows = page.locator("tbody tr")
    if await rows.count() > 0:
        await move_to(page, rows.first)
        await asyncio.sleep(SHORT)
        if await rows.count() > 1:
            await move_to(page, rows.nth(1))
            await asyncio.sleep(SHORT)

    await asyncio.sleep(LONG)
    print("  ✓ Scene 5 done")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE 6 — Admin Panel
# ═══════════════════════════════════════════════════════════════════════════════

async def scene_6(page: Page, base: str):
    print("  Scene 6: Admin Panel")

    # --- 6a: Dashboard ---
    await goto(page, "/admin", base)
    await wait_idle(page, LONG)

    # Hover over KPI stats
    kpis = page.locator(".divide-x > div, .divide-x > span")
    for i in range(min(await kpis.count(), 4)):
        await move_to(page, kpis.nth(i))
        await asyncio.sleep(0.5)

    # Hover quick-action cards
    for href in ["/admin/books", "/admin/users", "/admin/fines"]:
        card = page.locator(f'a[href="{href}"]').first
        if await visible(card, 1000):
            await move_to(page, card)
            await asyncio.sleep(0.4)

    await asyncio.sleep(MED)

    # --- 6b: Books Management — Add a Book ---
    await goto(page, "/admin/books", base)
    await wait_idle(page, MED)

    # Show the table
    await scroll(page, 200, 1.0)
    await asyncio.sleep(MED)

    # Click "Add Book"
    add_btn = page.locator("button:has-text('Add Book')").first
    if await visible(add_btn, 2000):
        await page.evaluate("window.scrollTo({top:0,behavior:'smooth'})")
        await asyncio.sleep(0.5)
        await click(page, add_btn, after=MED)

        # Fill in some fields
        title_field = page.get_by_label("Title").first
        if await visible(title_field, 2000):
            await type_text(page, title_field, "The Art of Programming")
            await asyncio.sleep(SHORT)

        author_field = page.get_by_label("Author").first
        if await visible(author_field, 2000):
            await type_text(page, author_field, "Donald Knuth")
            await asyncio.sleep(SHORT)

        isbn_field = page.get_by_label("ISBN").first
        if await visible(isbn_field, 1500):
            await type_text(page, isbn_field, "978-0201896831")
            await asyncio.sleep(SHORT)

        desc_field = page.get_by_label("Description").first
        if await visible(desc_field, 1500):
            await type_text(
                page, desc_field,
                "A comprehensive guide to the fundamental algorithms and data structures "
                "that form the basis of all modern software."
            )

        await asyncio.sleep(LONG)

        # Cancel — don't actually create
        cancel = page.locator("button:has-text('Cancel')").first
        if await visible(cancel, 1500):
            await click(page, cancel, after=MED)

    # --- 6c: Users — find user, view detail, waive a fine ---
    await goto(page, "/admin/users", base)
    await wait_idle(page, MED)

    # Click a user row (prefer one with outstanding fines)
    user_rows = page.locator("tbody tr")
    row_count = await user_rows.count()
    clicked_row = False
    for i in range(min(row_count, 15)):
        text = await user_rows.nth(i).inner_text()
        if "$" in text and "$0.00" not in text:
            await click(page, user_rows.nth(i), after=MED)
            clicked_row = True
            break
    if not clicked_row and row_count > 0:
        await click(page, user_rows.first, after=MED)

    await wait_idle(page, MED)

    # Show the user detail page — KPI bar and loans tab
    await asyncio.sleep(MED)

    # Switch to Fines tab
    fines_tab = page.locator("button:has-text('Fines')").first
    if await visible(fines_tab, 2000):
        await click(page, fines_tab, after=MED)

        # Hover a fine row to reveal the Waive button
        fine_rows = page.locator("tbody tr")
        if await fine_rows.count() > 0:
            await move_to(page, fine_rows.first)
            await asyncio.sleep(SHORT)

            # Click "Waive"
            waive = page.locator("button:has-text('Waive')").first
            if await visible(waive, 2000):
                await click(page, waive, after=LONG)
                await asyncio.sleep(LONG)

    # Switch to Loans tab to show loan management
    loans_tab = page.locator("button:has-text('Loans')").first
    if await visible(loans_tab, 2000):
        await click(page, loans_tab, after=MED)
        await asyncio.sleep(MED)

        # Hover a loan row to show Return / Mark Lost buttons
        loan_rows = page.locator("tbody tr")
        if await loan_rows.count() > 0:
            await move_to(page, loan_rows.first)
            await asyncio.sleep(LONG)

    # --- 6d: Admin Fines page ---
    await goto(page, "/admin/fines", base)
    await wait_idle(page, MED)

    # Show KPI bar (Outstanding, Collected, Waived)
    await asyncio.sleep(MED)

    # Click through filter tabs
    for label in ["Pending", "Paid", "Waived", "All"]:
        tab = page.locator(f"button:has-text('{label}')").first
        if await visible(tab, 1000):
            await click(page, tab, after=SHORT)

    await asyncio.sleep(LONG)

    print("  ✓ Scene 6 done")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

SCENES = {
    1: scene_1,
    2: scene_2,
    3: scene_3,
    4: scene_4,
    5: scene_5,
    6: scene_6,
}


async def main():
    parser = argparse.ArgumentParser(description="PageTurn Loom walkthrough recorder")
    parser.add_argument("--scenes", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6],
                        help="Which scenes to run (default: all)")
    parser.add_argument("--local", action="store_true",
                        help=f"Use {LOCAL_URL} instead of production")
    parser.add_argument("--no-video", action="store_true",
                        help="Skip Playwright video recording (use Loom/OBS instead)")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Speed multiplier: 0.5 = slower, 2.0 = faster (default: 1.0)")
    args = parser.parse_args()

    base = LOCAL_URL if args.local else PROD_URL

    # Apply speed multiplier
    global SHORT, MED, LONG, SCENE_GAP, TYPE_DELAY
    SHORT /= args.speed
    MED /= args.speed
    LONG /= args.speed
    SCENE_GAP /= args.speed
    TYPE_DELAY = int(TYPE_DELAY / args.speed)

    os.makedirs(RECORDING_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--window-size=1440,900", "--disable-blink-features=AutomationControlled"],
        )

        ctx_opts = {"viewport": VIEWPORT}
        if not args.no_video:
            ctx_opts["record_video_dir"] = RECORDING_DIR
            ctx_opts["record_video_size"] = VIEWPORT

        context = await browser.new_context(**ctx_opts)
        page = await context.new_page()

        # Auto-inject cursor on every page load
        await page.add_init_script(CURSOR_INIT_SCRIPT)

        # Navigate to the app for login
        await page.goto(base)
        await asyncio.sleep(1)

        print()
        print("=" * 56)
        print("  Log in to the app in the browser window.")
        print("  Use an ADMIN account for the full demo.")
        print("  Move your real cursor to the screen edge.")
        print("=" * 56)

        await asyncio.get_event_loop().run_in_executor(
            None, lambda: input("\n  Press Enter when logged in to start...\n")
        )

        print()
        print(f"  Recording scenes: {args.scenes}")
        print(f"  Target: {base}")
        print(f"  Speed: {args.speed}x")
        print()

        for i, scene_num in enumerate(args.scenes):
            fn = SCENES.get(scene_num)
            if not fn:
                print(f"  ⚠ Unknown scene {scene_num}, skipping")
                continue
            try:
                await fn(page, base)
            except Exception as e:
                print(f"  ⚠ Scene {scene_num} error: {e}")

            # Pause between scenes (except after the last one)
            if i < len(args.scenes) - 1:
                await asyncio.sleep(SCENE_GAP)

        print()
        print("=" * 56)
        print("  Walkthrough complete!")
        if not args.no_video:
            print(f"  Video will be saved to {RECORDING_DIR}/")
        print("=" * 56)

        await asyncio.get_event_loop().run_in_executor(
            None, lambda: input("\n  Press Enter to close browser and save video...\n")
        )

        await context.close()
        await browser.close()

    if not args.no_video:
        # List saved recordings
        for f in os.listdir(RECORDING_DIR):
            if f.endswith(".webm"):
                print(f"  Saved: {RECORDING_DIR}/{f}")

    print("  Done. Import into your editor to trim + add voiceover.")


if __name__ == "__main__":
    asyncio.run(main())

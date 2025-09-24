import asyncio
import random
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from playwright.async_api import async_playwright, TimeoutError

router = APIRouter()

MAX_TO_CONFIRM = 40
CONCURRENT_BROWSERS = 3

# ---------------- HELPERS ----------------
async def _login_to_facebook(page, username, password, queue: asyncio.Queue):
    await queue.put(f"[{username}] Logging in...")
    await page.goto("https://m.facebook.com")
    await page.locator('input[name="email"]').fill(username)
    await page.locator('input[name="pass"]').fill(password)
    await page.get_by_role("button", name="Log In").click()

    try:
        save_info_btn = page.get_by_role("button", name="Not now")
        main_feed = page.get_by_text("What's on your mind?")
        task_save = asyncio.create_task(save_info_btn.wait_for(state="visible", timeout=15000))
        task_feed = asyncio.create_task(main_feed.wait_for(state="visible", timeout=15000))
        done, pending = await asyncio.wait([task_save, task_feed], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

        if task_save in done:
            await queue.put(f"[{username}] Clicking 'Not now' for save info...")
            await save_info_btn.click()
            await main_feed.wait_for(state="visible", timeout=10000)
        await queue.put(f"[{username}] ✅ Login successful")
    except TimeoutError:
        await queue.put(f"[{username}] ❌ Login verification failed")
        await page.screenshot(path=f"login_failed_{username}.png")
        raise

async def confirm_friend_requests(page, queue: asyncio.Queue, max_to_confirm=MAX_TO_CONFIRM):
    await queue.put("Navigating to friend requests page...")
    await page.goto("https://m.facebook.com/friends/requests")
    await page.wait_for_load_state('domcontentloaded')
    await asyncio.sleep(10)

    confirmed_count = 0
    scroll_attempts = 0
    max_scroll_attempts = 40

    while confirmed_count < max_to_confirm and scroll_attempts < max_scroll_attempts:
        confirm_buttons = page.get_by_role('button').filter(has_text="Confirm")
        visible_buttons = await confirm_buttons.all()
        if not visible_buttons:
            scroll_attempts += 1
            await queue.put(f"No buttons found, scrolling... ({scroll_attempts}/{max_scroll_attempts})")
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(5)
            continue

        scroll_attempts = 0
        for btn in visible_buttons:
            if confirmed_count >= max_to_confirm:
                break
            try:
                await btn.click()
                confirmed_count += 1
                await queue.put(f"✅ Confirmed friend request #{confirmed_count}")
                await asyncio.sleep(random.uniform(5, 10))
            except Exception:
                await queue.put("⚠ Button disappeared, skipping.")

        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(5)

    await queue.put(f"✅ Finished confirming {confirmed_count} friend requests.")

async def process_account(username, password, queue: asyncio.Queue):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            await _login_to_facebook(page, username, password, queue)
            await confirm_friend_requests(page, queue)
        except Exception as e:
            await queue.put(f"⚠ Error for {username}: {e}")
            await page.screenshot(path=f"error_{username}.png")
        finally:
            await browser.close()
            await queue.put(f"[{username}] Browser closed")

# ---------------- ROUTE ----------------
@router.post("/facebook/auto_confirm")
async def auto_confirm_endpoint(data: dict = Body(...)):
    """
    JSON payload:
    {
        "accounts": [{"username": "u1", "password": "p1"}, ...],
        "max_to_confirm": 40,           # optional
        "concurrent_browsers": 3        # optional
    }
    """
    accounts = data.get("accounts", [])
    max_to_confirm = int(data.get("max_to_confirm", MAX_TO_CONFIRM))
    concurrent_browsers = int(data.get("concurrent_browsers", CONCURRENT_BROWSERS))

    if not accounts:
        return {"error": True, "message": "No accounts provided."}

    queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(concurrent_browsers)

    async def sem_task(username, password):
        async with semaphore:
            await process_account(username, password, queue)

    tasks = [sem_task(acc['username'], acc['password']) for acc in accounts]

    async def event_generator():
        task_group = asyncio.create_task(asyncio.gather(*tasks))
        try:
            while True:
                log = await queue.get()
                yield f"data: {log}\n\n"
                if log.startswith("✅ Finished confirming") or log.startswith("Browser closed"):
                    if all(t.done() for t in tasks):
                        break
        finally:
            if not task_group.done():
                task_group.cancel()
                try:
                    await task_group
                except asyncio.CancelledError:
                    pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")
import asyncio
import csv
import random
import re
from fastapi import APIRouter
from playwright.async_api import async_playwright

router = APIRouter()

CONCURRENCY_LIMIT = 3
PRE_ACTION_DELAY = 5
POST_ACTION_DELAY = 5
INTER_POST_DELAY = 5
# ---------------------

# --- CORE FUNCTIONS ---
async def _login_to_facebook(page, username, password, queue: asyncio.Queue):
    await queue.put(f"[{username}] Attempting to log in...")
    try:
        await page.goto("https://m.facebook.com", timeout=60000)
        await page.locator('input[name="email"]').fill(username)
        await page.locator('input[name="pass"]').fill(password)
        await page.get_by_role("button", name="Log In").click()
        await queue.put(f"[{username}] Login submitted. Waiting for verification...")

        save_info_button = page.get_by_role("button", name="Not now")
        main_feed_locator = page.get_by_text("What's on your mind?")

        task_save_info = asyncio.create_task(save_info_button.wait_for(state="visible", timeout=15000))
        task_main_feed = asyncio.create_task(main_feed_locator.wait_for(state="visible", timeout=15000))
        done, pending = await asyncio.wait([task_save_info, task_main_feed], return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()

        if task_save_info in done:
            await queue.put(f"[{username}] Detected 'Save Info' screen. Clicking 'Not now'...")
            await save_info_button.click()
            await main_feed_locator.wait_for(state="visible", timeout=10000)
        elif task_main_feed in done:
            await queue.put(f"[{username}] Landed directly on the main feed.")

        await queue.put(f"✅ [{username}] Login verification successful.")
        return True
    except Exception as e:
        await queue.put(f"❌ [{username}] Login failed: {e}")
        await page.screenshot(path=f"login_failed_{username}.png")
        return False

async def like_post(page, post_url, username, queue: asyncio.Queue):
    await queue.put(f"-> [{username}] Navigating to post: {post_url}")
    await page.goto(post_url, timeout=60000)
    await queue.put(f"   [{username}] Page loaded. Waiting {PRE_ACTION_DELAY}s...")
    await asyncio.sleep(PRE_ACTION_DELAY)

    like_button = page.get_by_role("button", name=re.compile("like", re.IGNORECASE)).first
    await queue.put(f"   [{username}] Searching for 'Like' button...")

    for i in range(10):
        if await like_button.is_visible():
            await queue.put(f"   ✅ [{username}] 'Like' button found after {i+1} attempts.")
            break
        await queue.put(f"   -> [{username}] Scrolling... (Attempt {i+1}/10)")
        await page.mouse.wheel(0, 800)
        await asyncio.sleep(2)
    else:
        await queue.put(f"   ❌ [{username}] Could not find 'Like' button.")
        await page.screenshot(path=f"like_button_not_found_{username}_{random.randint(1000,9999)}.png")
        return

    await queue.put(f"   [{username}] Clicking 'Like' button...")
    await like_button.click()
    await queue.put(f"   [{username}] Waiting {POST_ACTION_DELAY}s after like...")
    await asyncio.sleep(POST_ACTION_DELAY)
    await queue.put(f"   👍 [{username}] Finished with post.")

async def test_like_action(username, password, post_urls, queue: asyncio.Queue):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            login_ok = await _login_to_facebook(page, username, password, queue)
            if not login_ok:
                return

            await queue.put(f"[{username}] Starting to like {len(post_urls)} posts...")
            for i, url in enumerate(post_urls):
                await queue.put(f"--- [{username}] Processing URL {i+1}/{len(post_urls)} ---")
                await like_post(page, url, username, queue)
                if i < len(post_urls) - 1:
                    await queue.put(f"   ...waiting {INTER_POST_DELAY}s before next post.")
                    await asyncio.sleep(INTER_POST_DELAY)

        except Exception as e:
            await queue.put(f"❌ [{username}] Error: {e}")
            await page.screenshot(path=f"error_{username}.png")
        finally:
            await queue.put(f"✅ [{username}] Closing browser.")
            await browser.close()

async def run_like_task(accounts, post_urls, queue: asyncio.Queue, concurrency=3):
    if not accounts:
        await queue.put("❌ No accounts provided.")
        return
    await queue.put(f"Found {len(accounts)} account(s). Running with concurrency {concurrency}.")

    for i in range(0, len(accounts), concurrency):
        batch = accounts[i:i + concurrency]
        tasks = [test_like_action(user['username'], user['password'], post_urls, queue) for user in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        await queue.put(f"==================== Batch {i//concurrency+1} Finished ====================")

    await queue.put("🎉 All account batches processed.")

# backend/auto_add_friends_mobile_combined.py
import asyncio
import csv
import random
from playwright.async_api import async_playwright, TimeoutError
MAX_TO_ADD = 50               # Max friends to add per account
CONCURRENT_BROWSERS = 5       # Max simultaneous browsers


async def _login_to_facebook(page, username, password, send_log):
    await send_log(f"Logging in as {username}...")
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
            await send_log("Clicking 'Not now' for save info...")
            await save_info_btn.click()
            await main_feed.wait_for(state="visible", timeout=10000)
        await send_log(f"✅ Login successful for {username}")
    except TimeoutError:
        await send_log(f"❌ Login verification failed for {username}")
        await page.screenshot(path=f"login_failed_{username}.png")
        raise

async def add_multiple_friends_mobile(page, max_friends_to_add, send_log):
    await send_log("Navigating to friends page...")
    await page.goto("https://m.facebook.com/friends/")
    await page.wait_for_load_state('domcontentloaded')
    await asyncio.sleep(10)

    added_count = 0
    scroll_attempts = 0
    max_scroll_attempts = 100

    while added_count < max_friends_to_add and scroll_attempts < max_scroll_attempts:
        add_buttons_locator = page.get_by_role('button').filter(has_text="Add friend")
        visible_buttons = await add_buttons_locator.all()

        if not visible_buttons:
            scroll_attempts += 1
            await send_log(f"No buttons found, scrolling... ({scroll_attempts}/{max_scroll_attempts})")
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(5)
            continue

        scroll_attempts = 0
        for button in visible_buttons:
            if added_count >= max_friends_to_add:
                break
            try:
                await button.click()
                added_count += 1
                await send_log(f"✅ Sent friend request #{added_count}")
                await asyncio.sleep(random.uniform(8, 15))
            except Exception:
                await send_log("⚠ Button disappeared, skipping.")

        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(5)

    await send_log(f"✅ Finished. Sent a total of {added_count} friend requests.")

async def process_account(username, password, max_to_add, send_log):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            await _login_to_facebook(page, username, password, send_log)
            await add_multiple_friends_mobile(page, max_to_add, send_log)
        except Exception as e:
            await send_log(f"[ERROR] {username}: {e}")
            await page.screenshot(path=f"error_{username}.png")
        finally:
            await browser.close()

import asyncio
import re
import random
from playwright.async_api import async_playwright, TimeoutError

async def _login_to_facebook(page, username, password, queue: asyncio.Queue):
    await queue.put(f"[{username}] Attempting to log in...")
    try:
        await page.goto("https://m.facebook.com", timeout=60000)
        await page.locator('input[name="email"]').fill(username)
        await page.locator('input[name="pass"]').fill(password)
        await page.get_by_role('button', name="Log In").click()
        await queue.put(f"[{username}] Login submitted. Waiting for next page...")
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

        await queue.put(f"[{username}] ✅ Login verification successful.")
        return True
    except Exception as e:
        await queue.put(f"[{username}] ❌ Login failed: {e}")
        await page.screenshot(path=f"login_failed_{username}.png")
        return False

async def comment_on_post(page, post_url, comment_text, username, queue: asyncio.Queue):
    await queue.put(f"[{username}] -> Navigating to post: {post_url}")
    await page.goto(post_url, timeout=60000)
    await queue.put(f"[{username}] Waiting for page network to be idle...")
    await page.wait_for_load_state('networkidle', timeout=15000)

    comment_button = page.get_by_role("button", name="comment")
    await queue.put(f"[{username}] Finding the comment button...")
    for i in range(10):
        if await comment_button.is_visible():
            await queue.put(f"[{username}] ✅ Comment button found!")
            break
        await queue.put(f"[{username}] Scrolling down... (Attempt {i+1}/10)")
        await page.mouse.wheel(0, 800)
        await asyncio.sleep(2)
    else:
        raise TimeoutError(f"Could not find comment button.")

    await comment_button.click()
    comment_textbox = page.get_by_role("combobox", name="Write a comment…")
    await comment_textbox.wait_for(state="visible", timeout=10000)
    await queue.put(f"[{username}] Typing comment: {comment_text}")
    await comment_textbox.fill(comment_text)

    send_button = page.get_by_role("button", name=re.compile("Post|Send", re.IGNORECASE)).last
    await send_button.wait_for(state="visible", timeout=5000)
    await send_button.click()
    await page.wait_for_timeout(3000)
    await queue.put(f"[{username}] 💬 Comment submitted successfully.")

async def test_comment_action(username, password, post_urls, comment_list, queue: asyncio.Queue):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            login_successful = await _login_to_facebook(page, username, password, queue)
            if login_successful:
                await queue.put(f"[{username}] Starting comments on {len(post_urls)} posts...")
                for i, url in enumerate(post_urls):
                    try:
                        random_comment = random.choice(comment_list)
                        await comment_on_post(page, url, random_comment, username, queue)
                        await asyncio.sleep(random.uniform(8, 15))  # Human-like delay
                    except Exception as e:
                        await queue.put(f"[{username}] ❌ Error on URL {url}: {e}")
                        await page.screenshot(path=f"url_error_{username}_{i+1}.png")
        finally:
            await queue.put(f"[{username}] Closing browser.")
            await browser.close()

# Concurrency wrapper
async def run_account_with_semaphore(semaphore, username, password, post_urls, comments, queue):
    async with semaphore:
        await test_comment_action(username, password, post_urls, comments, queue)

async def run_multiple_accounts(accounts, post_urls, comments, max_concurrent=5, queue=None):
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [
        asyncio.create_task(
            run_account_with_semaphore(semaphore, acc['username'], acc['password'], post_urls, comments, queue)
        ) for acc in accounts
    ]
    await asyncio.gather(*tasks)
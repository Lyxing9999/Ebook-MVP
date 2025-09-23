import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError

async def _login_to_facebook(page, username, password, queue: asyncio.Queue):
    """Performs a robust login on m.facebook.com."""
    await queue.put(f"Attempting to log in as {username}...")
    await page.goto("https://m.facebook.com")
    
    await page.locator('input[name="email"]').fill(username)
    await page.locator('input[name="pass"]').fill(password)
    await page.get_by_role('button', name="Log In").click()

    await queue.put("Login submitted. Waiting for next page...")
    save_info_button = page.get_by_role("button", name="Not now")
    main_feed_locator = page.get_by_role("button", name="Make a Post on Facebook")

    try:
        task_save_info = asyncio.create_task(save_info_button.wait_for(state="visible", timeout=15000))
        task_main_feed = asyncio.create_task(main_feed_locator.wait_for(state="visible", timeout=15000))
        done, pending = await asyncio.wait([task_save_info, task_main_feed], return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()

        if task_save_info in done:
            await queue.put("Detected 'Save Info' screen. Clicking 'Not now'...")
            await save_info_button.click()
            await main_feed_locator.wait_for(state="visible", timeout=10000)
        elif task_main_feed in done:
            await queue.put("Landed directly on the main feed.")
        await queue.put("✅ Login verification successful.")
    except TimeoutError as e:
        await queue.put("❌ Login verification failed.")
        await page.screenshot(path="login_verification_failed.png")
        raise e

async def like_post(page, post_url, queue: asyncio.Queue):
    """Navigates to a post URL and clicks the 'Like' button."""
    await queue.put(f"Navigating to post: {post_url}")
    await page.goto(post_url)
    await page.wait_for_load_state('domcontentloaded')

    # Find the 'Like' button using a flexible regular expression
    like_button = page.get_by_role("button", name=re.compile("like", re.IGNORECASE)).first
    
    await like_button.wait_for(state="visible", timeout=10000)
    await queue.put("Found 'Like' button. Clicking...")
    await like_button.click()
    await page.wait_for_timeout(3000) # Wait a moment for the action to register
    await queue.put("✅ 'Like' action completed.")

async def auto_like(username, password, post_url, queue: asyncio.Queue):
    """Main function to run the test."""
    async with async_playwright() as p:
        # We run with headless=False so we can watch the test
        browser = await p.chromium.launch(
            headless=False,
        )
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            await _login_to_facebook(page, username, password, queue)
            await like_post(page, post_url, queue)
        except Exception as e:
            await queue.put(f"An error occurred during the test: {e}")
            await page.screenshot(path="like_action_error.png")
        finally:
            await queue.put("Test finished. Closing browser.")
            await browser.close()


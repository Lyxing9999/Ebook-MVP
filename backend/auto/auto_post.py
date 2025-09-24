import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError

import os

async def _login_to_facebook(page, username, password , queue: asyncio.Queue):
    await queue.put(f"[DEBUG] Logging in as {username}...")
    await page.goto("https://m.facebook.com")
    await page.locator('input[name="email"]').fill(username)
    await page.locator('input[name="pass"]').fill(password)
    await page.get_by_role('button', name="Log In").click()
    await queue.put("[DEBUG] Login submitted... waiting for feed.")

    # Handle 'Save Info' screen
    save_info_button = page.get_by_role("button", name="Not now")
    try:
        task_save_info = asyncio.create_task(save_info_button.wait_for(state="visible", timeout=10000))
        task_feed = asyncio.create_task(page.locator("div").filter(
            has_text=re.compile(r"^What's on your mind\?$")
        ).first.wait_for(state="visible", timeout=10000))

        done, pending = await asyncio.wait([task_save_info, task_feed], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

        if task_save_info in done:
            await queue.put("[DEBUG] Detected 'Save Info' screen, clicking Not now...")
            await save_info_button.click()
            # Wait for the post box after clicking
            await page.locator("div").filter(
                has_text=re.compile(r"^What's on your mind\?$")
            ).first.wait_for(state="visible", timeout=10000)

        await queue.put("[DEBUG] ✅ Login successful, feed loaded.")
    except TimeoutError:
        await queue.put("[ERROR] Feed did not load in time.")
        await page.screenshot(path="login_failed.png")
        raise

async def create_post(username, password, post_content, queue: asyncio.Queue):
    async with async_playwright() as p:
        # Set headless=False to actually see the browser
        browser = await p.chromium.launch(
            headless=False,
        )
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()

        try:
            await queue.put(f"[DEBUG] Logging in as {username}...")
            # Step 1: Login
            await _login_to_facebook(page, username, password, queue)
            await queue.put("[DEBUG] Login successful, now posting...")
            
            # Step 2: Locate the outer div with "What's on your mind?"
            post_div = page.locator("div").filter(has_text=re.compile(r"^What's on your mind\?$")).first
            await post_div.wait_for(state="visible", timeout=15000)

            # Step 3: Click to focus and type
            await post_div.click(force=True)
            await asyncio.sleep(1.5)
            await post_div.type(" " + post_content, delay=100)
            await queue.put("[DEBUG] Typed post content...")

            # Ensure content is fully typed before continuing
            await post_div.wait_for(state="attached", timeout=5000)  # Wait for the input to stay active
            await asyncio.sleep(2)

            # Step 5: Click POST button reliably only after typing content
            post_button = page.get_by_role("button", name="POST").first
            await post_button.wait_for(state="visible", timeout=15000)  # Ensure POST button is visible

            await queue.put("[DEBUG] Clicking POST button...")
            await post_button.click(force=True)

            await asyncio.sleep(3)
            
            # Confirm post appears in feed
            await asyncio.sleep(3)  # Wait for any delay in post processing

            # Wait for the post to appear in the feed
            post_locator = page.locator(f"div:has-text('{post_content.strip()}')").first

            # Wait for the post locator to be visible (with timeout and retries if necessary)
            try:
                await post_locator.wait_for(state="visible", timeout=30000)  # Wait for up to 30 seconds for post to appear
                await queue.put("✅ Post confirmed in feed!")
            except Exception as e:
                # If the post doesn't appear in time, log the failure
                await queue.put("❌ Post failed to appear in the feed.")
                await queue.put(f"[ERROR] {e}")
                    
        except Exception as e:
            await queue.put(f"[ERROR] An exception occurred: {e}")
            await page.screenshot(path="post_error.png")
            await queue.put("[DEBUG] Screenshot saved to 'post_error.png'")
        finally:
            await browser.close()
            await queue.put("[DEBUG] Browser closed.")
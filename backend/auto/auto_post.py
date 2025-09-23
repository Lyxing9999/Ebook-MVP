import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError

import os

async def _login_to_facebook(page, username, password):
    print(f"[DEBUG] Logging in as {username}...")
    await page.goto("https://m.facebook.com")
    await page.locator('input[name="email"]').fill(username)
    await page.locator('input[name="pass"]').fill(password)
    await page.get_by_role('button', name="Log In").click()
    print("[DEBUG] Login submitted... waiting for feed.")

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
            print("[DEBUG] Detected 'Save Info' screen, clicking Not now...")
            await save_info_button.click()
            # Wait for the post box after clicking
            await page.locator("div").filter(
                has_text=re.compile(r"^What's on your mind\?$")
            ).first.wait_for(state="visible", timeout=10000)

        print("[DEBUG] ✅ Login successful, feed loaded.")
    except TimeoutError:
        print("[ERROR] Feed did not load in time.")
        await page.screenshot(path="login_failed.png")
        raise

async def create_post(username, password, post_content):
    async with async_playwright() as p:
        # Set headless=False to actually see the browser
        browser = await p.chromium.launch(
            headless=False,
        )
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()

        try:
            yield f"[DEBUG] Logging in as {username}..."
            # Step 1: Login
            await _login_to_facebook(page, username, password)
            yield "[DEBUG] Login successful, now posting..."
            # Step 2: Locate the outer div with "What's on your mind?"
            post_div = page.locator("div").filter(has_text=re.compile(r"^What's on your mind\?$")).first
            await post_div.wait_for(state="visible", timeout=15000)

            # Step 3: Click to focus and type

            await post_div.click(force=True)
            await asyncio.sleep(1.5)
            await post_div.type(" " + post_content, delay=100)
            yield "[DEBUG] Typed post content..."
            await asyncio.sleep(2)
            # Step 5: Click POST button reliably
            post_button = page.get_by_role("button", name="POST").first
            await post_button.wait_for(state="visible", timeout=15000)
            await asyncio.sleep(1)
            yield "[DEBUG] Clicked POST button..."
            await post_button.click(force=True)

            await asyncio.sleep(3)
            # Confirm post
            posted = await page.locator(f"div:has-text('{post_content.strip()}')").first.is_visible()
            yield "✅ Post confirmed in feed!" if posted else "⚠️ Post may have failed."

        except Exception as e:
            yield f"[ERROR] An exception occurred: {e}"
            await page.screenshot(path="post_error.png")
            yield "[DEBUG] Screenshot saved to 'post_error.png'"
        finally:
            await browser.close()
            yield "[DEBUG] Browser closed."

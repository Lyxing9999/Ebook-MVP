# auto_comment.py (FINAL, WORKING VERSION WITH SCROLLING)
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

async def comment_on_post(page, post_url, comment_text, queue: asyncio.Queue):
    """Navigates to a post and writes a comment on the mobile site."""
    await queue.put(f"Navigating to post: {post_url}")
    await page.goto(post_url)
    await page.wait_for_load_state('domcontentloaded')

    # STEP 1: Scroll down until the comment button is visible
    await queue.put("Finding the comment button by scrolling...")
    comment_button = page.get_by_role("button", name="comment")
    
    # Loop up to 10 times, scrolling each time, to find the button
    for i in range(10):
        if await comment_button.is_visible():
            await queue.put("Comment button found!")
            break
        await queue.put(f"Button not visible, scrolling down... (Attempt {i+1}/10)")
        # Simulate a mouse wheel scroll down the page
        await page.mouse.wheel(0, 800)
        await page.wait_for_timeout(1000) # Wait a moment for content to load
    else:
        # If the loop finishes without finding the button
        await queue.put("❌ Could not find the comment button after scrolling.")
        raise TimeoutError("Comment button not found on the page.")

    await comment_button.click()
    
    # STEP 2: Find the comment input box using a more reliable placeholder locator
    await queue.put("Finding the comment text box...")
    comment_textbox = page.get_by_role("combobox", name="Write a comment…")
    await comment_textbox.wait_for(state="visible", timeout=10000)
    
    # STEP 3: Type the comment using .fill() which is better for text areas
    await queue.put(f"Typing comment: '{comment_text}'")
    await comment_textbox.fill(comment_text)
    
    # STEP 4: Find and click the 'Send' button
    await queue.put("Finding the send button...")
    # Use a more specific locator for the send/post button
    send_button = page.get_by_role("button", name=re.compile("Post|Send", re.IGNORECASE)).last
    await send_button.wait_for(state="visible", timeout=5000)
    await send_button.click()
    
    await page.wait_for_timeout(3000)
    await queue.put("✅ Comment submitted successfully.")


async def auto_comment(username, password, post_url, comment , queue: asyncio.Queue):
    """Main function to run the test."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            await _login_to_facebook(page, username, password, queue)
            await comment_on_post(page, post_url, comment, queue)
        except Exception as e:
            await queue.put(f"An error occurred during the test: {e}")
            await page.screenshot(path="comment_action_error.png")
        finally:
            await queue.put("Test finished. Closing browser.")
            await browser.close()


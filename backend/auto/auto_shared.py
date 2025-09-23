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

async def share_post(page, post_url, queue: asyncio.Queue):
    """Navigates to a post and performs the full three-step share action."""
    await queue.put(f"Navigating to post: {post_url}")
    await page.goto(post_url)
    await page.wait_for_load_state('domcontentloaded')

    # STEP 1: Find and click the initial 'Share' button
    await queue.put("Step 1: Finding and clicking the 'Share' button...")
    share_button = page.get_by_role("button", name="Share")
    await share_button.wait_for(state="visible", timeout=10000)
    await share_button.click()
    
    # STEP 2: Find and click the 'Share to Facebook' button
    await queue.put("Step 2: Finding and clicking the 'Share to Facebook' button...")
    share_to_facebook_button = page.get_by_label("Share to Facebook")
    await share_to_facebook_button.wait_for(state="visible", timeout=10000)
    await share_to_facebook_button.click()

    # STEP 3: Find and click the final 'POST' button
    await queue.put("Step 3: Finding and clicking the final 'POST' button...")
    post_button = page.get_by_role("button", name="POST", exact=True)
    await post_button.wait_for(state="visible", timeout=10000)
    await post_button.click()
    
    await page.wait_for_timeout(3000)
    await queue.put("✅ Share action completed successfully.")


async def auto_share(username, password, post_url, queue: asyncio.Queue):
    """Main function to run the test."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
        )
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            await _login_to_facebook(page, username, password, queue)
            await share_post(page, post_url, queue)
        except Exception as e:
            await queue.put(f"An error occurred during the test: {e}")
            await page.screenshot(path="share_action_error.png")
        finally:
            await queue.put("Test finished. Closing browser.")
            await browser.close()

# if __name__ == "__main__":
#     test_username = "61579016878362"
#     test_password = "somalasam025#"
#     test_post_url = "https://m.facebook.com/photo?fbid=122096033390967229&set=a.122096033420967229"

#     if "YOUR_TEST_USERNAME" in test_username or "..." in test_post_url:
#         print("Please update the test credentials and post URL at the bottom of the script.")
#     else:
#         asyncio.run(test_share_action(test_username, test_password, test_post_url))

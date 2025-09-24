# backend/auto_share.py
import asyncio
import csv
from playwright.async_api import async_playwright, TimeoutError

# ---------------- LOGIN FUNCTION ----------------
async def _login_to_facebook(page, username, password, queue: asyncio.Queue):
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
        for task in pending:
            task.cancel()

        if task_save_info in done:
            await queue.put("Detected 'Save Info' screen. Clicking 'Not now'...")
            await save_info_button.click()
            await main_feed_locator.wait_for(state="visible", timeout=10000)
        elif task_main_feed in done:
            await queue.put("Landed directly on the main feed.")
        await queue.put("✅ Login successful.")
    except TimeoutError:
        await queue.put("❌ Login verification failed.")
        await page.screenshot(path=f"{username}_login_failed.png")
        raise

# ---------------- SHARE FUNCTION ----------------
async def share_post(page, post_url, queue: asyncio.Queue):
    await queue.put(f"Navigating to post: {post_url}")
    await page.goto(post_url)
    await page.wait_for_load_state('domcontentloaded')

    await page.wait_for_timeout(5000)  # wait 5s before sharing

    await queue.put("Step 1: Clicking 'Share'...")
    share_button = page.get_by_role("button", name="Share")
    await share_button.wait_for(state="visible", timeout=10000)
    await share_button.click()

    await queue.put("Step 2: Clicking 'Share to Facebook'...")
    share_to_facebook_button = page.get_by_label("Share to Facebook")
    await share_to_facebook_button.wait_for(state="visible", timeout=10000)
    await share_to_facebook_button.click()
    await page.wait_for_timeout(3000)  # wait 3s

    await queue.put("Step 3: Clicking 'POST'...")
    post_button = page.get_by_role("button", name="POST", exact=True)
    await post_button.wait_for(state="visible", timeout=10000)
    await post_button.click()
    await page.wait_for_timeout(5000)  # wait 5s after post

    await queue.put("✅ Share completed.")

# ---------------- MAIN TASK PER ACCOUNT ----------------
async def run_account(username, password, links, queue: asyncio.Queue):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=0)
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            await _login_to_facebook(page, username, password, queue)
            for link in links:
                await share_post(page, link, queue)
        except Exception as e:
            await queue.put(f"⚠️ Error for {username}: {e}")
            await page.screenshot(path=f"{username}_error.png")
        finally:
            await queue.put(f"Finished for {username}, closing browser.")
            await browser.close()

# ---------------- BATCH RUNNER ----------------
async def run_all_accounts(accounts, links, queue: asyncio.Queue, max_parallel=3):
    for i in range(0, len(accounts), max_parallel):
        batch = accounts[i:i+max_parallel]
        tasks = [run_account(username, password, links, queue) for username, password in batch]
        await asyncio.gather(*tasks)
    await queue.put("🎉 All shares completed!")


# ---------------- MAIN ----------------
# async def main():
#     # Load accounts from accounts.csv
#     accounts = []
#     with open("accounts.csv", newline="", encoding="utf-8") as f:
#         reader = csv.reader(f)
#         for row in reader:
#             if len(row) >= 2:
#                 accounts.append((row[0], row[1]))

#     # Links directly in the script
#     links = [
#         "https://www.facebook.com/photo/?fbid=2129459380680067&set=a.203435464481565",
#         "https://www.facebook.com/photo/?fbid=2066478950311444&set=a.203435464481565",
#         "https://www.facebook.com/photo/?fbid=2025078654451474&set=a.203435464481565",
#     ]

#     if not accounts or not links:
#         print("⚠️ No accounts or links found. Please update accounts.csv or links in the script")
#         return

#     await run_all_accounts(accounts, links, max_parallel=3)

# if __name__ == "__main__":
#     asyncio.run(main())

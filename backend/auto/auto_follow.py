import asyncio
import random
import re
import csv
import os
from playwright.async_api import async_playwright, TimeoutError

async def _login_to_facebook(page, username, password, queue: asyncio.Queue):
    """Performs a robust login on m.facebook.com."""
    await queue.put(f"[{username}] Attempting to log in...")
    # Go to the mobile site for login, as we are emulating an iPhone
    await page.goto("https://m.facebook.com")
    
    await page.locator('input[name="email"]').fill(username)
    await page.locator('input[name="pass"]').fill(password)
    await page.get_by_role('button', name="Log In").click()

    await queue.put(f"[{username}] Login submitted. Waiting for next page...")
    save_info_button = page.get_by_role("button", name="Not now")
    
    # Looks for "What's on your mind?" to confirm login was successful
    main_feed_locator = page.get_by_text("What's on your mind?")

    try:
        # Check if either the "Save Info" screen or the main feed appears
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
    except TimeoutError as e:
        await queue.put(f"[{username}] ❌ Login verification failed.")
        await page.screenshot(path="login_verification_failed_mobile.png")
        raise e

async def follow_pages_from_list(page, page_urls , queue: asyncio.Queue):
    """Navigates to a list of pages and follows them with delays."""
    await queue.put("\nStarting to follow pages...")
    followed_count = 0
    for i, url in enumerate(page_urls):
        await queue.put(f"--- Processing page {i+1}/{len(page_urls)}: {url} ---")
        try:
            # 1. Navigate to the page
            await page.goto(url)
            await page.wait_for_load_state('domcontentloaded', timeout=15000)
            
            # --- NEW CODE: Wait 5 seconds AFTER navigating ---
            await queue.put("   -> Page loaded. Waiting for 5 seconds before action...")
            await asyncio.sleep(5)
            # --- END OF NEW CODE ---
            
            action_taken = False

            # 2. Find and click the follow button
            # This locator uses a regular expression to find a button with an accessible name that STARTS with "Follow".
            follow_button = page.get_by_role("button", name=re.compile(r"^Follow", re.IGNORECASE)).first
            
            if await follow_button.is_visible(timeout=5000):
                await follow_button.click()
                action_taken = True
                await queue.put(f"   -> ✅ Clicked the 'Follow' button!")
            else:
                # If the "Follow" button wasn't found, check if it's because we are already following.
                following_button = page.get_by_role('button', name='Following').first
                if await following_button.is_visible(timeout=2000):
                    await queue.put("   -> Already following. Skipping.")
                else:
                    await queue.put(f"   -> ❌ Could not find a 'Follow' button. The page might be a type that cannot be followed, or you may have already liked it.")
                    await page.screenshot(path=f"follow_page_failed_{i+1}.png")

            # If we took an action, increment the counter and wait
            if action_taken:
                followed_count += 1
                await queue.put(f"   -> Total followed in this session: {followed_count}")
                
                # 3. Wait 5 seconds AFTER clicking
                sleep_time = 5
                await queue.put(f"   -> Waiting for {sleep_time} seconds before moving to the next page...")
                await asyncio.sleep(sleep_time)

        except Exception as e:
            await queue.put(f"   -> ❌ An unexpected error occurred on page {url}: {e}")
            await page.screenshot(path=f"follow_page_error_{i+1}.png")

    await queue.put(f"\n✅ Finished. Followed a total of {followed_count} new pages.")

async def run_follow_process_for_account(username, password, urls_to_follow, queue: asyncio.Queue):
    """Main function to run the auto-following process for a single account."""
    async with async_playwright() as p:
        # Use headless=True to run in the background, or headless=False to watch the browser
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(**p.devices['iPhone 13'])
        page = await context.new_page()
        try:
            await _login_to_facebook(page, username, password , queue)
            await follow_pages_from_list(page, urls_to_follow, queue)
        except Exception as e:
            await queue.put(f"An error occurred during the process for {username}: {e}")
            await page.screenshot(path=f"error_{username}.png")
        finally:
            await queue.put(f"Process finished for {username}. Closing browser.")
            await browser.close()






# --- STANDALONE EXECUTION BLOCK ---
if __name__ == "__main__":
    # The script will look for this file in the same directory
    ACCOUNTS_FILE = 'accounts.csv'
    
    # --- IMPORTANT: ADD THE FACEBOOK PAGE LINKS YOU WANT TO FOLLOW HERE ---
    PAGES_TO_FOLLOW = [
        "https://www.facebook.com/belteischool",
        "https://www.facebook.com/PositivityInspiresPage",
        "https://www.facebook.com/ActressEiChawPoOfficialPage",
       
        # Add more page or profile URLs here, for example:
        # "https://www.facebook.com/therock"
    ]
    

    # --- SCRIPT LOGIC ---
    if not PAGES_TO_FOLLOW:
        print("❌ Please add URLs to the PAGES_TO_FOLLOW list in the script.")
    elif not os.path.exists(ACCOUNTS_FILE):
        print(f"❌ Error: The file '{ACCOUNTS_FILE}' was not found.")
        print("   Please create it and add accounts, with each line formatted as: username,password")
    else:
        accounts = []
        with open(ACCOUNTS_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                # Ensure the row has at least two non-empty columns
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    accounts.append({'username': row[0].strip(), 'password': row[1].strip()})
        
        if not accounts:
            print(f"❌ No valid accounts found in '{ACCOUNTS_FILE}'. Please check the format.")
        else:
            print(f"✅ Found {len(accounts)} account(s) to process from '{ACCOUNTS_FILE}'.")
            for i, account in enumerate(accounts):
                username = account['username']
                password = account['password']
                
                print(f"\n{'='*50}")
                print(f"🚀 Starting process for account {i+1}/{len(accounts)}: {username}")
                print(f"{'='*50}")
                
                try:
                    asyncio.run(run_follow_process_for_account(username, password, PAGES_TO_FOLLOW))
                    print(f"\n✅ Successfully finished process for account: {username}")
                except Exception as e:
                    print(f"\n❌ A critical error occurred while processing account {username}: {e}")
            
            print(f"\n{'='*50}")
            print("🎉 All accounts have been processed.")
            print(f"{'='*50}")
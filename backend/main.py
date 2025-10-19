# backend/main.py
import os
from fastapi import FastAPI, Request, Query, Body
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from auto.auto_post import create_post
from auto.auto_like import auto_like
from auto.auto_comment import auto_comment
from auto.comment_multiple_links import run_multiple_accounts
import asyncio
app = FastAPI()

# Account
from account.route import router as accounts_router
app.include_router(accounts_router)

# Auth
from auth.auth import router as auth_router
app.include_router(auth_router)


# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Playwright browsers path
os.makedirs("/tmp/.playwright", exist_ok=True)
os.chmod("/tmp/.playwright", 0o777)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/Users/kaingbunly/.playwright"


@app.get("/facebook/post")
async def auto_post_endpoint(username: str = Query(...), password: str = Query(...), content: str = Query(...)):
    queue = asyncio.Queue()
    async def event_generator():
        task = asyncio.create_task(create_post(username, password, content, queue))
        try:
            while True:
                log = await queue.get()
                yield f"data: {log}\n\n"
                if log.startswith("Test finished"):
                    break
        finally:
            task.cancel()
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/facebook/auto_like")
async def auto_like_endpoint(username: str = Query(...), password: str = Query(...), post_url: str = Query(...)):
    queue = asyncio.Queue()
    async def event_generator():
        # Start auto_like_action as a background task
        task = asyncio.create_task(auto_like(username, password, post_url, queue))
        try:
            while True:
                log = await queue.get()
                yield f"data: {log}\n\n"
                if log.startswith("Test finished"):
                    
                    break
        finally:
            task.cancel()
    return StreamingResponse(event_generator(), media_type="text/event-stream")





@app.get("/facebook/auto_comment")
async def auto_comment_endpoint(username: str = Query(...), password: str = Query(...), post_url: str = Query(...), comment: str = Query(...)):
    queue = asyncio.Queue()
    async def event_generator():

        try:
            task = asyncio.create_task(auto_comment(username, password, post_url, comment, queue))
            while True:
                try:
                    log = await asyncio.wait_for(queue.get(), timeout=180)
                except asyncio.TimeoutError:
                    yield f"data: [ERROR] Queue timeout.\n\n"
                    break
                yield f"data: {log}\n\n"
                if log.startswith("Test finished"):
                    break
        finally:
            task.cancel()
    return StreamingResponse(event_generator(), media_type="text/event-stream")



# @app.get("/facebook/auto_share")
# async def auto_share_endpoint(username: str = Query(...), password: str = Query(...), post_url: str = Query(...)):
#     queue = asyncio.Queue()
#     async def event_generator():
#         try:
#             task = asyncio.create_task(auto_share(username, password, post_url, queue))
#             while True:
#                 try:
#                     log = await asyncio.wait_for(queue.get(), timeout=180)
#                 except asyncio.TimeoutError:
#                     yield f"data: [ERROR] Queue timeout.\n\n"
#                     break
#                 yield f"data: {log}\n\n"
#                 if log.startswith("Test finished"):
#                     break
#         finally:
#             task.cancel()
#     return StreamingResponse(event_generator(), media_type="text/event-stream")







#Auto Post With Multiple  



@app.post("/facebook/auto_comment_multi")
async def auto_comment_multi_endpoint(data: dict = Body(...)):
    """
    Expects JSON payload:
    {
        "accounts": [{"username": "u1", "password": "p1"}, ...],
        "posts": ["https://m.facebook.com/..."],
        "comments": ["Great post!", "Nice!"],
        "concurrency": 3  # optional, default 5
    }
    """
    accounts = data.get("accounts", [])
    posts = data.get("posts", [])
    comments = data.get("comments", [])
    concurrency = data.get("concurrency", 5)

    if not accounts or not posts or not comments:
        return {"error": True, "message": "accounts, posts, and comments are required."}
    queue: asyncio.Queue = asyncio.Queue()
    async def event_generator():
        task = asyncio.create_task(
            run_multiple_accounts(accounts, posts, comments, max_concurrent=concurrency, queue=queue)
        )
        try:
            while True:
                log = await queue.get()
                yield f"data: {log}\n\n"
                if log.startswith("All posts processed.") or log.startswith("Closing browser."):
                    # optional: break if all logs done
                    break
        finally:
            task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")



from auto.auto_follow import run_follow_process_for_account
# FastAPI route to start the follow process
@app.post("/facebook/auto_follow_multi")
async def auto_follow_multi_endpoint(data: dict = Body(...)):
    """
    Expects JSON payload:
    {
        "accounts": [{"username": "user1", "password": "pass1"}, ...],
        "urls_to_follow": ["https://m.facebook.com/page1", "https://m.facebook.com/page2"],

    }
    """
    accounts = data.get("accounts", [])
    urls_to_follow = data.get("urls_to_follow", [])

    if not accounts or not urls_to_follow:
        return {"error": True, "message": "accounts and urls_to_follow are required."}

    queue: asyncio.Queue = asyncio.Queue()

    # Modify run_follow_process_for_account to return the queue for streaming logs
    async def event_generator():
        tasks = []
        for acc in accounts:
            # Start each follow process for account
            task = asyncio.create_task(run_follow_process_for_account(acc['username'], acc['password'], urls_to_follow, queue))
            tasks.append(task)

        try:
            # Yield logs from all tasks
            while True:
                log = await queue.get()
                yield f"data: {log}\n\n"
                if log.startswith("Process finished"):
                    if all(task.done() for task in tasks):
                        break
        finally:
            for task in tasks:
                task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

from auto.like_multiple_chroms import run_like_task

@app.post("/facebook/auto_like")
async def auto_like_endpoint(data: dict = Body(...)):
    """
    Expects JSON payload from frontend:
    {
        "accounts": [{"username": "u1", "password": "p1"}, ...],
        "post_urls": ["https://...","https://..."],
        "concurrency": 3  # optional
    }
    """
    accounts = data.get("accounts", [])
    post_urls = data.get("post_urls", [])
    concurrency = data.get("concurrency", 3)

    if not accounts or not post_urls:
        return {"error": True, "message": "accounts and post_urls are required."}

    queue = asyncio.Queue()

    async def event_generator():
        task = asyncio.create_task(run_like_task(accounts, post_urls, queue, concurrency))
        try:
            while True:
                log = await queue.get()
                yield f"data: {log}\n\n"
                if "🎉 All account batches processed." in log:
                    break
        finally:
            task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


CONCURRENCY_LIMIT = 3
from auto.shared_multiple import run_all_accounts


# -----------------------------
# Auto-share endpoint
# -----------------------------
@app.post("/facebook/auto_share")
async def auto_share(data: dict = Body(...)):
    """
    Expects JSON payload:
    {
        "accounts": [{"username": "u1", "password": "p1"}, ...] OR ["u1", "u2"],
        "post_urls": ["https://...", "https://..."],
        "concurrency": 3  # optional
    }
    """
    accounts = data.get("accounts", [])
    links = data.get("post_urls", [])
    concurrency = int(data.get("concurrency", CONCURRENCY_LIMIT))

    if not accounts or not links:
        return {"error": True, "message": "accounts and post_urls are required."}

    # Normalize accounts: allow strings or dicts
    normalized_accounts = []
    for acc in accounts:
        if isinstance(acc, str):
            normalized_accounts.append({"username": acc, "password": ""})
        elif isinstance(acc, dict) and "username" in acc:
            normalized_accounts.append(acc)

    queue: asyncio.Queue = asyncio.Queue()

    async def event_generator():
        task = asyncio.create_task(run_all_accounts(normalized_accounts, links, queue, concurrency))
        try:
            while True:
                msg = await queue.get()
                yield f"data: {msg}\n\n"
                if msg.startswith("🎉 All shares completed!"):
                    break
        finally:
            task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")



from auto.confirm_friends import process_account, MAX_TO_CONFIRM, CONCURRENT_BROWSERS


@app.post("/facebook/auto_confirm_multi")
async def auto_confirm_endpoint(data: dict = Body(...)):
    """
    JSON payload:
    {
        "accounts": [{"username": "u1", "password": "p1"}, ...],
        "max_to_confirm": 40,           # optional
        "concurrent_browsers": 3        # optional
    }
    """
    accounts = data.get("accounts", [])
    max_to_confirm = int(data.get("max_to_confirm", MAX_TO_CONFIRM))
    concurrent_browsers = int(data.get("concurrent_browsers", CONCURRENT_BROWSERS))

    if not accounts:
        return {"error": True, "message": "No accounts provided."}

    queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(concurrent_browsers)

    async def sem_task(username, password):
        async with semaphore:
            await process_account(username, password, queue)

    tasks = [sem_task(acc['username'], acc['password']) for acc in accounts]

    async def event_generator():
        task_group = asyncio.create_task(asyncio.gather(*tasks))
        try:
            while True:
                log = await queue.get()
                yield f"data: {log}\n\n"
                if log.startswith("✅ Finished confirming") or log.startswith("Browser closed"):
                    if all(t.done() for t in tasks):
                        break
        finally:
            if not task_group.done():
                task_group.cancel()
                try:
                    await task_group
                except asyncio.CancelledError:
                    pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")

from auto.add_friends import process_account , MAX_TO_ADD, CONCURRENT_BROWSERS, add_multiple_friends_mobile

@app.post("/facebook/auto_add_friends_multi")
async def auto_add_friends_multi_endpoint(request: Request):
    data = await request.json()
    accounts = data.get("accounts", [])
    max_to_add = data.get("max_to_add", 50)
    concurrent_browsers = data.get("concurrent_browsers", 5)

    async def event_generator():
        semaphore = asyncio.Semaphore(concurrent_browsers)

        async def sem_task(acc):
            async with semaphore:
                queue = asyncio.Queue()

                async def send_log(msg):
                    await queue.put(f"data: {msg}\n\n")

                async def run_task():
                    await process_account(acc['username'], acc['password'], max_to_add, send_log)
                    await queue.put(None)

                task = asyncio.create_task(run_task())

                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    yield item

        for acc in accounts:
            async for message in sem_task(acc):
                yield message

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
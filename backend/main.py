# backend/main.py
import os
from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from auto.auto_post import create_post
from auto.auto_like import auto_like
from auto.auto_comment import auto_comment
from auto.auto_shared import auto_share
import asyncio
from account.route import router as accounts_router
app = FastAPI()
app.include_router(accounts_router)
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
    if not all([username, password, content]):
        return JSONResponse({"error": "Missing fields"}, status_code=400)

    async def event_generator():
        try:
            async for log in create_post(username, password, content):
                yield f"data: {log}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

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



@app.get("/facebook/auto_share")
async def auto_share_endpoint(username: str = Query(...), password: str = Query(...), post_url: str = Query(...)):
    queue = asyncio.Queue()
    async def event_generator():
        try:
            task = asyncio.create_task(auto_share(username, password, post_url, queue))
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



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
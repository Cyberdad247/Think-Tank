from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
import asyncio
import redis
from celery import Celery
import json

# Load environment variables
load_dotenv()

# FastAPI app setup
app = FastAPI()

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

# Celery app setup
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

@app.post("/api/debate")
async def debate_endpoint(request: Request):
    data = await request.json()
    query = data.get("query")
    task = celery_app.send_task("tasks.process_query", args=[query])
    return {"message": "Query received, processing started", "task_id": task.id}

@app.get("/api/debate/stream")
async def debate_stream(request: Request):
    async def event_generator():
        pubsub = redis_client.pubsub()
        pubsub.subscribe("debate_progress")
        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                if await request.is_disconnected():
                    break
        except asyncio.CancelledError:
            pass
        finally:
            pubsub.unsubscribe("debate_progress")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
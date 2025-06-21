from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
import asyncio
import redis
from celery import Celery
from celery.exceptions import CeleryError
import json
import logging

# Configure logging
# Basic config is set here, can be overridden by a more sophisticated setup if the app grows
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

from think_tank_monorepo.packages.cache_queue.redis_client import get_redis_client, get_redis_url

# FastAPI app setup
app = FastAPI()

# Shared Redis client setup
# Attempt to initialize the shared Redis client on startup.
# If this fails, the application might not be able to start or will be unhealthy.
shared_redis_client = get_redis_client()

if not shared_redis_client:
    logger.critical("Failed to initialize shared Redis client. Application might not work correctly.")
    # Depending on the desired behavior, you might raise an exception here to stop the app
    # raise RuntimeError("Failed to initialize shared Redis client.")
else:
    logger.info(f"Shared Redis client successfully initialized for FastAPI app from URL: {get_redis_url()}")


# Celery app setup
# Ensure Celery uses the same Redis URL that the shared client was configured with.
CELERY_REDIS_URL = get_redis_url() # Get the URL, which might have been constructed from parts
celery_app = Celery("tasks", broker=CELERY_REDIS_URL, backend=CELERY_REDIS_URL)
logger.info(f"Celery app configured with broker and backend URL: {CELERY_REDIS_URL}")


@app.post("/api/debate")
async def debate_endpoint(request: Request):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    query = data.get("query")
    if not query or not isinstance(query, str) or not query.strip():
        raise HTTPException(status_code=400, detail="Field 'query' is missing, empty, or not a string.")

    try:
        task = celery_app.send_task("tasks.process_query", args=[query])
        return {"message": "Query received, processing started", "task_id": task.id}
    except CeleryError as e: # More specific exception for Celery related issues
        logger.error(f"Celery task sending failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Could not send task to broker.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in /api/debate: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/debate/stream")
async def debate_stream(request: Request):
    async def event_generator():
        pubsub = None
        if not shared_redis_client:
            logger.error("Redis client not available for debate_stream.")
            # Optionally yield an error to the client and then stop
            yield f"data: {json.dumps({'error': 'Stream temporarily unavailable due to server error.'})}\n\n"
            return

        try:
            pubsub = shared_redis_client.pubsub()
            await pubsub.subscribe("debate_progress") # Use await for async pubsub if client supports it, check redis-py async usage
            logger.info("Subscribed to debate_progress channel for streaming.")

            # Note: redis-py's pubsub.listen() is typically blocking.
            # For FastAPI's async context, an async version or running listen in a thread might be needed
            # if the pubsub client itself is not async-compatible in this version.
            # Assuming shared_redis_client.pubsub() and listen() are compatible with asyncio here based on prior code.
            # If using redis-py's async client (redis.asyncio as redis), then methods would be `await pubsub.listen()` etc.
            # The existing code `async for message in pubsub.listen()` implies it's handled.

            async for message in pubsub.listen():
                if message["type"] == "message":
                    logger.debug(f"Received message: {message['data']}")
                    yield f"data: {message['data']}\n\n"

                if await request.is_disconnected():
                    logger.info("Client disconnected, closing stream.")
                    break
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error in debate_stream: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': 'Stream interrupted due to connection error.'})}\n\n"
        except asyncio.CancelledError:
            logger.info("Debate stream task cancelled.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in debate_stream: {e}", exc_info=True)
            # yield f"data: {json.dumps({'error': 'An unexpected error occurred in the stream.'})}\n\n"
        finally:
            if pubsub:
                try:
                    logger.info("Unsubscribing from debate_progress and closing pubsub connection.")
                    await pubsub.unsubscribe("debate_progress") # use await if client is async
                    await pubsub.close() # use await if client is async
                except Exception as e:
                    logger.error(f"Error during pubsub cleanup: {e}", exc_info=True)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    logger.info(f"Starting Uvicorn server on {APP_HOST}:{APP_PORT}")
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
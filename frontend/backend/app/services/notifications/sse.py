import asyncio
import os
import json
import logging
import redis.asyncio as redis
from sse_starlette.sse import EventSourceResponse
from fastapi import Request

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)
    return redis_client

async def publish_notification(channel: str, message: dict):
    """Publish a notification to a specific channel (e.g., 'notifications:admin')."""
    try:
        r = await get_redis()
        await r.publish(channel, json.dumps(message))
        logger.info(f"Published to {channel}: {message}")
    except Exception as e:
        logger.error(f"Failed to publish notification: {e}")

async def sse_generator(request: Request, channel: str):
    """Generator for Server-Sent Events that yields messages from a Redis channel."""
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    
    logger.info(f"SSE Client subscribed to {channel}")
    
    try:
        while True:
            if await request.is_disconnected():
                logger.info(f"SSE Client disconnected from {channel}")
                break
                
            # Wait for message with timeout to check for disconnects
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                yield {
                    "event": "message",
                    "data": message["data"]
                }
            await asyncio.sleep(0.1) # Small sleep to prevent tight loop
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()

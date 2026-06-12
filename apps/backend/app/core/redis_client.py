from __future__ import annotations

import logging

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis


async def redis_available() -> bool:
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception:
        return False

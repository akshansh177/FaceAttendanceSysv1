from __future__ import annotations

import time

from app.core.redis_client import get_redis


async def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Returns True if request is allowed."""
    redis = await get_redis()
    now = int(time.time())
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_seconds)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window_seconds)
    results = await pipe.execute()
    count = results[2]
    return count <= limit

from __future__ import annotations

import logging
import os
import uuid

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

LEADER_KEY = "cron:leader"
LEADER_TTL = 120


async def acquire_leader_lock() -> bool:
    """Return True if this process should run scheduled jobs."""
    try:
        redis = await get_redis()
    except Exception:
        return False
    try:
        instance_id = f"{os.getpid()}:{uuid.uuid4().hex[:8]}"
        acquired = await redis.set(LEADER_KEY, instance_id, nx=True, ex=LEADER_TTL)
        if acquired:
            return True
        current = await redis.get(LEADER_KEY)
        if current and (
            isinstance(current, bytes) and current.decode() == instance_id or current == instance_id
        ):
            await redis.expire(LEADER_KEY, LEADER_TTL)
            return True
        return False
    except Exception as e:
        logger.debug("Leader lock unavailable: %s", e)
        return False


async def refresh_leader_lock() -> None:
    try:
        redis = await get_redis()
        if await redis.exists(LEADER_KEY):
            await redis.expire(LEADER_KEY, LEADER_TTL)
    except Exception:
        pass

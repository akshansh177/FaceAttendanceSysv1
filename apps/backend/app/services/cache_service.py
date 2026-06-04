from __future__ import annotations

import json
from typing import Any, Callable, TypeVar

from app.core.redis_client import get_redis

T = TypeVar("T")

ENTITY_TTL = 900  # 15 minutes


async def cache_get(key: str) -> str | None:
    redis = await get_redis()
    val = await redis.get(key)
    return val.decode() if isinstance(val, bytes) else val


async def cache_set(key: str, value: str, ttl: int = ENTITY_TTL) -> None:
    redis = await get_redis()
    await redis.setex(key, ttl, value)


async def cache_delete_prefix(prefix: str) -> None:
    redis = await get_redis()
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=f"{prefix}*", count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break


async def get_or_load_json(key: str, loader: Callable[[], Any], ttl: int = ENTITY_TTL) -> Any:
    cached = await cache_get(key)
    if cached:
        return json.loads(cached)
    data = await loader()
    await cache_set(key, json.dumps(data, default=str), ttl=ttl)
    return data


async def invalidate_entity_caches() -> None:
    await cache_delete_prefix("cache:departments")
    await cache_delete_prefix("cache:job_roles")
    await cache_delete_prefix("cache:shifts")
    await cache_delete_prefix("cache:locations")
    await cache_delete_prefix("cache:policies")
    await cache_delete_prefix("cache:settings")


async def invalidate_dashboard_cache() -> None:
    from datetime import date

    redis = await get_redis()
    today = date.today().isoformat()
    await redis.delete(f"dashboard:metrics:{today}")
    await cache_delete_prefix("dashboard:trends:")

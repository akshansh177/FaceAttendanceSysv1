from __future__ import annotations

import asyncio
import logging

from app.core.database import async_session
from app.core.redis_client import get_redis
from app.services.face_service import rebuild_embedding_index

logger = logging.getLogger(__name__)

INDEX_RELOAD_CHANNEL = "faiss:index:reload"
_redis_wait_logged = False


async def publish_index_reload() -> None:
    redis = await get_redis()
    await redis.publish(INDEX_RELOAD_CHANNEL, "1")


async def index_reload_listener() -> None:
    global _redis_wait_logged
    while True:
        try:
            redis = await get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe(INDEX_RELOAD_CHANNEL)
            _redis_wait_logged = False
            try:
                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    try:
                        async with async_session() as db:
                            n = await rebuild_embedding_index(db)
                            await db.commit()
                            logger.info("FAISS index reloaded from pub/sub (%s vectors)", n)
                    except Exception as e:
                        logger.warning("FAISS pub/sub reload failed: %s", e)
            finally:
                await pubsub.unsubscribe(INDEX_RELOAD_CHANNEL)
                await pubsub.close()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if not _redis_wait_logged:
                logger.warning(
                    "Index sync waiting for Redis (%s). Local dev: docker compose -f docker-compose.dev.yml up -d",
                    e,
                )
                _redis_wait_logged = True
            await asyncio.sleep(30)

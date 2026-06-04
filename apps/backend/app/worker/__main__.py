"""Background worker: cron leader jobs + export queue (no HTTP server)."""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import async_session
from app.services.archive_jobs import run_archive_job
from app.services.attendance_engine import mark_missing_checkouts, recompute_all_summaries
from app.services.cron_leader import acquire_leader_lock, refresh_leader_lock
from app.services.export_jobs import process_export_queue_once
from app.services.notification_jobs import send_daily_hr_alerts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def nightly_jobs():
    if not await acquire_leader_lock():
        return
    async with async_session() as db:
        try:
            count = await recompute_all_summaries(db)
            missing = await mark_missing_checkouts(db)
            alerts = await send_daily_hr_alerts(db)
            await run_archive_job(db)
            await db.commit()
            logger.info("Worker nightly: recomputed=%s missing=%s alerts=%s", count, missing, alerts)
        except Exception as e:
            await db.rollback()
            logger.error("Worker nightly failed: %s", e)


async def summary_interval_jobs():
    if not await acquire_leader_lock():
        return
    await refresh_leader_lock()
    async with async_session() as db:
        try:
            count = await recompute_all_summaries(db)
            await db.commit()
            logger.debug("Worker interval summary: %s", count)
        except Exception as e:
            await db.rollback()
            logger.error("Worker interval failed: %s", e)


async def export_worker_loop():
    while True:
        try:
            if await acquire_leader_lock():
                await refresh_leader_lock()
                processed = True
                while processed:
                    processed = await process_export_queue_once()
        except Exception as e:
            logger.error("Export worker error: %s", e)
        await asyncio.sleep(2)


async def main():
    scheduler.add_job(nightly_jobs, "cron", hour=23, minute=30)
    scheduler.add_job(summary_interval_jobs, "interval", minutes=5)
    scheduler.start()
    logger.info("Backend worker started")
    await export_worker_loop()


if __name__ == "__main__":
    asyncio.run(main())

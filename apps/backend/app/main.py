from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Histogram, make_asgi_app

API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request duration",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

from app.api import (
    attendance,
    audit,
    auth,
    corrections,
    dashboard,
    departments,
    devices,
    employees,
    faces,
    holidays,
    job_roles,
    kiosk,
    kiosks,
    leaves,
    locations,
    me,
    policies,
    reports,
    settings as settings_api,
    shifts,
)
from app.core.config import get_settings
from app.core.database import async_session
from app.services.attendance_engine import mark_missing_checkouts, recompute_all_summaries
from app.services.cron_leader import acquire_leader_lock, refresh_leader_lock
from app.services.export_jobs import process_export_queue_once
from app.services.face_service import rebuild_embedding_index
from app.services.index_sync import index_reload_listener
from app.services.notification_jobs import send_daily_hr_alerts
from app.services.policy_service import warm_policy_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
_export_worker_task: asyncio.Task | None = None
_index_listener_task: asyncio.Task | None = None


async def nightly_jobs():
    if not await acquire_leader_lock():
        return
    async with async_session() as db:
        try:
            count = await recompute_all_summaries(db)
            missing = await mark_missing_checkouts(db)
            alerts = await send_daily_hr_alerts(db)
            await db.commit()
            logger.info(
                "Nightly jobs: recomputed=%s missing_checkout=%s hr_alerts=%s",
                count,
                missing,
                alerts,
            )
        except Exception as e:
            await db.rollback()
            logger.error("Nightly jobs failed: %s", e)


async def summary_interval_jobs():
    if not await acquire_leader_lock():
        return
    await refresh_leader_lock()
    async with async_session() as db:
        try:
            count = await recompute_all_summaries(db)
            await db.commit()
            logger.debug("Interval summary recompute: %s employees", count)
        except Exception as e:
            await db.rollback()
            logger.error("Interval summary failed: %s", e)


async def export_worker_loop():
    while True:
        try:
            if await acquire_leader_lock():
                await refresh_leader_lock()
                await process_export_queue_once()
        except Exception as e:
            logger.error("Export worker error: %s", e)
        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _export_worker_task, _index_listener_task
    async with async_session() as db:
        try:
            n = await rebuild_embedding_index(db, broadcast=False)
            await warm_policy_cache(db)
            await db.commit()
            logger.info("Startup: FAISS index loaded (%s vectors)", n)
        except Exception as e:
            logger.warning("Startup index rebuild failed: %s", e)

    scheduler.add_job(nightly_jobs, "cron", hour=23, minute=30)
    scheduler.add_job(summary_interval_jobs, "interval", minutes=5)
    scheduler.start()
    _export_worker_task = asyncio.create_task(export_worker_loop())
    _index_listener_task = asyncio.create_task(index_reload_listener())
    yield
    if _export_worker_task:
        _export_worker_task.cancel()
    if _index_listener_task:
        _index_listener_task.cancel()
    scheduler.shutdown()


app_settings = get_settings()
app = FastAPI(title="Face Attendance API", version="3.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/api/"):
        API_REQUEST_DURATION.labels(method=request.method, path=path.split("?")[0][:80]).observe(
            time.perf_counter() - start
        )
    return response

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(departments.router)
app.include_router(job_roles.router)
app.include_router(locations.router)
app.include_router(shifts.router)
app.include_router(faces.router)
app.include_router(attendance.router)
app.include_router(corrections.router)
app.include_router(holidays.router)
app.include_router(leaves.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(settings_api.router)
app.include_router(devices.router)
app.include_router(kiosk.router)
app.include_router(kiosks.router)
app.include_router(policies.router)
app.include_router(me.router)
app.include_router(audit.router)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health():
    from app.services.embedding_index import get_embedding_index

    idx = get_embedding_index()
    return {
        "status": "ok",
        "service": "backend",
        "version": "3.1.0",
        "faiss_vectors": idx.size,
        "faiss_version": idx.version,
    }

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from app.core.redis_client import get_redis
from app.core.database import async_session
from app.services import export as export_svc
from app.services import reports as report_svc

QUEUE_KEY = "export:queue"
JOB_PREFIX = "export:job:"


async def enqueue_export(job_type: str, params: dict, fmt: str, user_id: str) -> str:
    job_id = str(uuid.uuid4())
    redis = await get_redis()
    payload = {
        "id": job_id,
        "type": job_type,
        "params": params,
        "format": fmt,
        "user_id": user_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await redis.setex(f"{JOB_PREFIX}{job_id}", 3600, json.dumps(payload))
    await redis.rpush(QUEUE_KEY, job_id)
    return job_id


async def get_job(job_id: str) -> dict | None:
    redis = await get_redis()
    raw = await redis.get(f"{JOB_PREFIX}{job_id}")
    if not raw:
        return None
    return json.loads(raw)


async def _update_job(job_id: str, patch: dict) -> None:
    job = await get_job(job_id)
    if not job:
        return
    job.update(patch)
    redis = await get_redis()
    await redis.setex(f"{JOB_PREFIX}{job_id}", 3600, json.dumps(job))


async def process_export_queue_once() -> bool:
    redis = await get_redis()
    job_id = await redis.lpop(QUEUE_KEY)
    if not job_id:
        return False
    if isinstance(job_id, bytes):
        job_id = job_id.decode()
    job = await get_job(job_id)
    if not job:
        return True
    await _update_job(job_id, {"status": "processing"})
    try:
        async with async_session() as db:
            params = job["params"]
            fmt = job["format"]
            report_type = job["type"]
            if report_type == "daily":
                from datetime import date

                d = date.fromisoformat(params["date"])
                rows = await report_svc.daily_report(db, d, params.get("department_id"))
                filename = f"daily_{d}.csv"
            elif report_type == "monthly":
                rows = await report_svc.monthly_report(
                    db, int(params["year"]), int(params["month"]), params.get("department_id")
                )
                filename = f"monthly_{params['year']}_{params['month']}.csv"
            else:
                rows = []
                filename = "export.csv"
            if fmt == "xlsx":
                content = export_svc.to_excel(rows)
                media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif fmt == "pdf":
                content = export_svc.to_pdf(rows, title=report_type)
                media = "application/pdf"
            else:
                content = export_svc.to_csv(rows)
                media = "text/csv"
            import base64

            await _update_job(
                job_id,
                {
                    "status": "completed",
                    "filename": filename,
                    "media_type": media,
                    "content_b64": base64.b64encode(content).decode("ascii"),
                },
            )
    except Exception as e:
        await _update_job(job_id, {"status": "failed", "error": str(e)})
    return True

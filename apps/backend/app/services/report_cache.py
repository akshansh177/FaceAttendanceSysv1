from __future__ import annotations

import json
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.schemas.schemas import ReportRow
from app.services import reports as report_svc

REPORT_TTL = 600


async def cached_daily_report(
    db: AsyncSession, report_date: date, department_id=None, force: bool = False
) -> list[ReportRow]:
    key = f"report:daily:{report_date.isoformat()}:{department_id or 'all'}"
    redis = await get_redis()
    if not force:
        cached = await redis.get(key)
        if cached:
            data = json.loads(cached)
            return [ReportRow(**row) for row in data]
    rows = await report_svc.daily_report(db, report_date, department_id)
    await redis.setex(key, REPORT_TTL, json.dumps([r.model_dump(mode="json", by_alias=True) for r in rows]))
    return rows


async def cached_monthly_report(
    db: AsyncSession, year: int, month: int, department_id=None, force: bool = False
) -> list[ReportRow]:
    key = f"report:monthly:{year}-{month:02d}:{department_id or 'all'}"
    redis = await get_redis()
    if not force:
        cached = await redis.get(key)
        if cached:
            data = json.loads(cached)
            return [ReportRow(**row) for row in data]
    rows = await report_svc.monthly_report(db, year, month, department_id)
    await redis.setex(key, REPORT_TTL, json.dumps([r.model_dump(mode="json", by_alias=True) for r in rows]))
    return rows

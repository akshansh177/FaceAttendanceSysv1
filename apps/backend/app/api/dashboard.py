from __future__ import annotations

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.models import User, UserRole
from app.core.redis_client import get_redis
from app.schemas.schemas import DashboardMetrics, DashboardTrends, EmployeeDashboard, LiveFeedItem
from app.services.dashboard import (
    get_employee_dashboard,
    get_manager_metrics,
    get_metrics,
    get_trends,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

MANAGER_ROLES = (UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.TEAM_MANAGER)
HR_ROLES = (UserRole.SUPER_ADMIN, UserRole.HR_MANAGER)


@router.get("/metrics", response_model=DashboardMetrics)
async def metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role in HR_ROLES:
        return await get_metrics(db)
    if user.role == UserRole.TEAM_MANAGER and user.employee_id:
        return await get_manager_metrics(db, user.employee_id)
    return await get_metrics(db)


@router.get("/hr", response_model=DashboardMetrics)
async def hr_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    return await get_metrics(db)


@router.get("/manager", response_model=DashboardMetrics)
async def manager_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.TEAM_MANAGER, UserRole.SUPER_ADMIN))],
):
    if not user.employee_id:
        return await get_metrics(db)
    return await get_manager_metrics(db, user.employee_id)


@router.get("/employee", response_model=EmployeeDashboard)
async def employee_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if not user.employee_id:
        return EmployeeDashboard(today_status=None, workflow_status=None, monthly_present=0, monthly_absent=0)
    return await get_employee_dashboard(db, user.employee_id)


@router.get("/trends", response_model=DashboardTrends)
async def trends(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    days: int = Query(default=30, ge=7, le=90),
):
    return await get_trends(db, days)


@router.get("/live-feed", response_model=list[LiveFeedItem])
async def live_feed(
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
    limit: int = Query(default=50, le=200),
):
    redis = await get_redis()
    raw = await redis.lrange("attendance:feed", 0, limit - 1)
    items = []
    for entry in raw:
        try:
            data = json.loads(entry)
            items.append(LiveFeedItem(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    return items


@router.get("/live-feed/stream")
async def live_feed_stream(
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    async def event_generator():
        redis = await get_redis()
        last_len = 0
        while True:
            raw = await redis.lrange("attendance:feed", 0, 49)
            if len(raw) != last_len or raw:
                payload = []
                for entry in raw:
                    try:
                        payload.append(json.loads(entry))
                    except (json.JSONDecodeError, TypeError):
                        continue
                yield f"data: {json.dumps(payload)}\n\n"
                last_len = len(raw)
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

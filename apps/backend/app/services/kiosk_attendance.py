from __future__ import annotations

import json
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.redis_client import get_redis
from app.models.models import (
    AttendanceKiosk,
    AttendanceLog,
    AttendanceSummary,
    Employee,
    EmployeeStatus,
    WorkflowStatus,
)
from app.services.attendance_engine import process_daily_summary
from app.services.settings_service import get_org_settings


async def record_kiosk_attendance(
    db: AsyncSession,
    employee: Employee,
    score: float,
    kiosk: AttendanceKiosk,
    action: str,
) -> tuple[str, str, str]:
    """Returns (event, status_level, code). action is check_in or check_out."""
    settings = get_settings()
    org = await get_org_settings(db)
    redis = await get_redis()
    dup_key = f"att:kiosk:{employee.id}:{action}"
    if await redis.exists(dup_key):
        return "duplicate", "warning", "attendance_already_recorded"

    now = datetime.now(timezone.utc)
    today = now.date()

    result = await db.execute(
        select(AttendanceSummary).where(
            and_(AttendanceSummary.employee_id == employee.id, AttendanceSummary.date == today)
        )
    )
    summary = result.scalar_one_or_none()

    log = AttendanceLog(
        employee_id=employee.id,
        timestamp=now,
        device_id=kiosk.device_identifier,
        kiosk_id=kiosk.id,
        recognition_score=score,
        event_type=action,
    )

    if action == "check_in":
        if summary and summary.check_in and not summary.check_out:
            return "already_checked_in", "warning", "already_checked_in"
        if summary and summary.check_out:
            return "already_checked_out", "warning", "already_checked_out"
        if not summary:
            summary = AttendanceSummary(employee_id=employee.id, date=today, check_in=now)
            summary.workflow_status = WorkflowStatus.CHECKED_IN
            db.add(summary)
        else:
            summary.check_in = now
            summary.workflow_status = WorkflowStatus.CHECKED_IN
        log.event_type = "check_in"
        db.add(log)
        event, code, level = "check_in", "check_in_success", "success"
    elif action == "check_out":
        if not summary or not summary.check_in:
            return "no_check_in", "warning", "no_check_in_today"
        if summary.check_out:
            if org.kiosk_checkout_after_checkout == "update":
                summary.check_out = now
                log.event_type = "check_out_update"
                db.add(log)
                event, code, level = "check_out_update", "attendance_updated", "success"
            else:
                return "already_checked_out", "warning", "already_checked_out"
        else:
            summary.check_out = now
            summary.workflow_status = WorkflowStatus.CHECKED_OUT
            log.event_type = "check_out"
            db.add(log)
            event, code, level = "check_out", "check_out_success", "success"
    else:
        return "invalid_action", "error", "face_not_recognized"

    await db.flush()
    emp_result = await db.execute(
        select(Employee).where(Employee.id == employee.id).options(selectinload(Employee.shift))
    )
    emp = emp_result.scalar_one()
    await process_daily_summary(db, emp, today)
    await redis.setex(dup_key, settings.duplicate_window_seconds, "1")

    from app.services.cache_service import invalidate_dashboard_cache

    await invalidate_dashboard_cache()
    await publish_feed_event(db, employee, kiosk, log, event)
    return event, level, code


async def publish_feed_event(
    db: AsyncSession,
    employee: Employee,
    kiosk: AttendanceKiosk,
    log: AttendanceLog,
    event: str,
) -> None:
    redis = await get_redis()
    emp_result = await db.execute(
        select(Employee)
        .where(Employee.id == employee.id)
        .options(
            selectinload(Employee.department),
            selectinload(Employee.job_role),
        )
    )
    emp = emp_result.scalar_one()
    payload = {
        "id": str(log.id),
        "employee_name": emp.full_name,
        "employee_code": emp.employee_code,
        "department": emp.department.name if emp.department else None,
        "job_role": emp.job_role.name if emp.job_role else None,
        "event_type": event,
        "timestamp": log.timestamp.isoformat(),
        "kiosk_name": kiosk.name,
        "location": kiosk.location.name if getattr(kiosk, "location", None) else None,
    }
    await redis.lpush("attendance:feed", json.dumps(payload))
    await redis.ltrim("attendance:feed", 0, 499)


def build_employee_display(employee: Employee) -> dict:
    photo = None
    if employee.profile_photo_path:
        photo = f"/uploads/{employee.profile_photo_path.split('/')[-1]}"
    return {
        "employee_id": employee.id,
        "photo_url": photo,
        "full_name": employee.full_name,
        "employee_code": employee.employee_code,
        "department": employee.department.name if employee.department else None,
        "job_role": employee.job_role.name if employee.job_role else None,
    }


def check_employee_active(employee: Employee) -> tuple[bool, str | None]:
    if employee.status != EmployeeStatus.ACTIVE:
        return False, "employee_disabled"
    return True, None

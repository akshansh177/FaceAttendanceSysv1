from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import HR_ROLES, MANAGER_ROLES, get_current_user, require_roles
from app.core.redis_client import get_redis
from app.models.models import AttendanceLog, AttendanceSummary, Employee, User, UserRole, WorkflowStatus
from app.schemas.schemas import AttendanceSummaryResponse, MessageResponse, RecognizeResponse
from app.services.attendance_channel import assert_channel_allowed
from app.services.attendance_engine import mark_missing_checkouts, process_daily_summary, recompute_all_summaries
from app.services.attendance_validators import validate_attendance_context
from app.services.face_service import find_best_match
from app.services.rate_limit import check_rate_limit
from app.services.recognition_client import recognition_client

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


async def _record_attendance(
    db: AsyncSession,
    employee: Employee,
    score: float,
    device_id: str | None,
    event_type: str = "recognize",
) -> tuple[str, bool]:
    settings = get_settings()
    redis = await get_redis()
    dup_key = f"att:{employee.id}"
    if await redis.exists(dup_key):
        return "duplicate", True

    now = datetime.now(timezone.utc)
    today = now.date()
    log = AttendanceLog(
        employee_id=employee.id,
        timestamp=now,
        device_id=device_id,
        recognition_score=score,
        event_type=event_type,
    )
    db.add(log)

    result = await db.execute(
        select(AttendanceSummary).where(
            and_(AttendanceSummary.employee_id == employee.id, AttendanceSummary.date == today)
        )
    )
    summary = result.scalar_one_or_none()
    if not summary:
        summary = AttendanceSummary(employee_id=employee.id, date=today, check_in=now)
        summary.workflow_status = WorkflowStatus.CHECKED_IN
        db.add(summary)
        event = "check_in"
    elif not summary.check_out:
        summary.check_out = now
        summary.workflow_status = WorkflowStatus.CHECKED_OUT
        event = "check_out"
    else:
        summary.check_out = now
        summary.workflow_status = WorkflowStatus.CHECKED_OUT
        event = "check_out_update"

    await db.flush()
    await db.refresh(employee, attribute_names=["shift"])
    emp_result = await db.execute(
        select(Employee).where(Employee.id == employee.id).options(selectinload(Employee.shift))
    )
    emp = emp_result.scalar_one()
    await process_daily_summary(db, emp, today)
    await redis.setex(dup_key, settings.duplicate_window_seconds, "1")
    from app.services.cache_service import invalidate_dashboard_cache

    await invalidate_dashboard_cache()
    return event, False


@router.post("/recognize", response_model=RecognizeResponse)
async def recognize(
    request: Request,
    file: UploadFile = File(...),
    device_id: str | None = Form(None),
    device_mac: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else "unknown"
    allowed = await check_rate_limit(f"rl:recognize:{client_ip}", 30, 60)
    if not allowed:
        raise HTTPException(429, "Rate limit exceeded")

    await assert_channel_allowed(db, "recognize")

    image_bytes = await file.read()
    resp = await recognition_client.detect_and_embed(image_bytes)
    if not resp or not resp.get("embedding"):
        return RecognizeResponse(matched=False, message="No face detected")

    from app.services.match_settings import get_effective_match_threshold

    settings = get_settings()
    match_threshold = await get_effective_match_threshold(db)
    match = await find_best_match(db, resp["embedding"])
    score = match.score
    employee_id = match.employee_id

    if match.ambiguous:
        return RecognizeResponse(matched=False, score=score, message="Ambiguous match")

    if score < settings.gray_zone_low:
        return RecognizeResponse(matched=False, score=score, message="No matching employee found")

    if (
        employee_id
        and settings.gray_zone_low <= score < match_threshold
        and settings.deepface_enabled
    ):
        ref = await db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        emp = ref.scalar_one_or_none()
        if emp and emp.profile_photo_path:
            from pathlib import Path
            photo_path = Path(settings.upload_dir) / emp.profile_photo_path
            if photo_path.is_file():
                ref_bytes = photo_path.read_bytes()
                verified = await recognition_client.verify_deepface(image_bytes, ref_bytes)
                if verified and not verified.get("verified"):
                    return RecognizeResponse(matched=False, score=score, message="Secondary verification failed")

    if score < match_threshold or not employee_id:
        return RecognizeResponse(
            matched=False, score=score, message="Match below threshold"
        )

    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.locations))
    )
    employee = result.scalar_one_or_none()
    if not employee:
        return RecognizeResponse(matched=False, message="Employee not found")

    valid, reason = await validate_attendance_context(
        db, request, employee, latitude, longitude, device_id, device_mac
    )
    if not valid:
        log = AttendanceLog(
            employee_id=employee.id,
            device_id=device_id,
            recognition_score=score,
            event_type="rejected",
            latitude=latitude,
            longitude=longitude,
            rejection_reason=reason,
        )
        db.add(log)
        return RecognizeResponse(matched=False, score=score, message=reason or "Validation failed")

    event, duplicate = await _record_attendance(db, employee, score, device_id)
    if duplicate:
        return RecognizeResponse(
            matched=True,
            employee_id=employee.id,
            employee_name=employee.full_name,
            score=score,
            message="Attendance already recorded recently",
            duplicate=True,
        )

    return RecognizeResponse(
        matched=True,
        employee_id=employee.id,
        employee_name=employee.full_name,
        score=score,
        event=event,
        message=f"Attendance recorded: {event}",
    )


@router.post("/checkin", response_model=MessageResponse)
async def manual_checkin(
    employee_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    await assert_channel_allowed(db, "portal")
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.shift))
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(404, "Employee not found")
    today = date.today()
    now = datetime.now(timezone.utc)
    summary_result = await db.execute(
        select(AttendanceSummary).where(
            and_(AttendanceSummary.employee_id == employee_id, AttendanceSummary.date == today)
        )
    )
    summary = summary_result.scalar_one_or_none()
    if not summary:
        summary = AttendanceSummary(employee_id=employee_id, date=today, check_in=now)
        db.add(summary)
    else:
        summary.check_in = now
    await process_daily_summary(db, employee, today)
    return MessageResponse(message="Check-in recorded")


@router.post("/checkout", response_model=MessageResponse)
async def manual_checkout(
    employee_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    await assert_channel_allowed(db, "portal")
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.shift))
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(404, "Employee not found")
    today = date.today()
    now = datetime.now(timezone.utc)
    summary_result = await db.execute(
        select(AttendanceSummary).where(
            and_(AttendanceSummary.employee_id == employee_id, AttendanceSummary.date == today)
        )
    )
    summary = summary_result.scalar_one_or_none()
    if not summary:
        raise HTTPException(400, "No check-in for today")
    summary.check_out = now
    await process_daily_summary(db, employee, today)
    return MessageResponse(message="Check-out recorded")


@router.get("/me", response_model=list[AttendanceSummaryResponse])
async def my_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    from_date: date | None = None,
    to_date: date | None = None,
):
    if not user.employee_id:
        return []
    q = select(AttendanceSummary).where(AttendanceSummary.employee_id == user.employee_id)
    if from_date:
        q = q.where(AttendanceSummary.date >= from_date)
    if to_date:
        q = q.where(AttendanceSummary.date <= to_date)
    result = await db.execute(q.order_by(AttendanceSummary.date.desc()))
    return result.scalars().all()


@router.get("/employee/{employee_id}", response_model=list[AttendanceSummaryResponse])
async def employee_attendance(
    employee_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    from_date: date | None = None,
    to_date: date | None = None,
):
    q = select(AttendanceSummary).where(AttendanceSummary.employee_id == employee_id)
    if from_date:
        q = q.where(AttendanceSummary.date >= from_date)
    if to_date:
        q = q.where(AttendanceSummary.date <= to_date)
    result = await db.execute(q.order_by(AttendanceSummary.date.desc()))
    return result.scalars().all()


@router.get("/summary", response_model=list[AttendanceSummaryResponse])
async def daily_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    report_date: date = Query(default_factory=date.today),
):
    result = await db.execute(
        select(AttendanceSummary).where(AttendanceSummary.date == report_date)
    )
    return result.scalars().all()


@router.post("/recompute", response_model=MessageResponse)
async def recompute(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER))],
    target_date: date | None = None,
):
    count = await recompute_all_summaries(db, target_date)
    return MessageResponse(message=f"Recomputed {count} summaries")

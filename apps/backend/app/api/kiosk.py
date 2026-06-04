from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import AttendanceLog, Employee, EmployeeStatus
from app.schemas.schemas import KioskConfigResponse, KioskRecognizeResponse, MessageResponse
from app.services.attendance_channel import assert_channel_allowed
from app.services.attendance_validators import validate_attendance_context
from app.services.face_service import find_best_match
from app.services.kiosk_attendance import (
    build_employee_display,
    check_employee_active,
    record_kiosk_attendance,
)
from app.services.kiosk_auth import authenticate_kiosk
from app.services.policy_service import validate_kiosk_policy
from app.services.rate_limit import check_rate_limit
from app.services.recognition_client import recognition_client
from app.services.settings_service import get_org_settings

router = APIRouter(prefix="/api/kiosk", tags=["kiosk"])


async def _get_kiosk(
    device_identifier: str = Form(...),
    x_kiosk_key: str = Header(..., alias="X-Kiosk-Key"),
    db: AsyncSession = Depends(get_db),
):
    return await authenticate_kiosk(db, device_identifier, x_kiosk_key)

MESSAGES = {
    "check_in_success": "Check In Successful",
    "check_out_success": "Check Out Successful",
    "already_checked_in": "Already Checked In Today",
    "already_checked_out": "Already Checked Out",
    "no_check_in_today": "Check In First Before Check Out",
    "attendance_already_recorded": "Attendance Already Recorded",
    "attendance_updated": "Attendance Updated",
    "face_not_recognized": "Face Not Recognized",
    "employee_disabled": "Employee Disabled",
    "device_not_authorized": "Device Not Authorized",
    "location_not_allowed": "Location Not Allowed",
    "liveness_failed": "Liveness Check Failed",
}


@router.get("/config", response_model=KioskConfigResponse)
async def kiosk_config(db: AsyncSession = Depends(get_db)):
    org = await get_org_settings(db)
    return KioskConfigResponse(
        screen_reset_seconds=org.kiosk_screen_reset_seconds,
        voice_feedback_enabled=org.voice_feedback_enabled,
        voice_language=org.voice_language,
    )


@router.post("/heartbeat", response_model=MessageResponse)
async def heartbeat(
    device_identifier: str = Form(...),
    db: AsyncSession = Depends(get_db),
    kiosk=Depends(_get_kiosk),
):
    if kiosk.device_identifier != device_identifier:
        raise HTTPException(400, "Device identifier mismatch")
    kiosk.last_seen = datetime.now(timezone.utc)
    return MessageResponse(message="ok")


@router.post("/recognize", response_model=KioskRecognizeResponse)
async def kiosk_recognize(
    request: Request,
    device_identifier: str = Form(...),
    action: str = Form(...),
    files: list[UploadFile] = File(...),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    client_event_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    kiosk=Depends(_get_kiosk),
):
    if kiosk.device_identifier != device_identifier:
        raise HTTPException(400, "Device identifier mismatch")
    if action not in ("check_in", "check_out"):
        raise HTTPException(400, "action must be check_in or check_out")
    if client_event_id:
        from app.core.redis_client import get_redis

        redis = await get_redis()
        dedupe_key = f"kiosk:event:{client_event_id}"
        if await redis.exists(dedupe_key):
            return KioskRecognizeResponse(
                matched=True,
                status="success",
                code="attendance_already_recorded",
                display_message=MESSAGES["attendance_already_recorded"],
            )
        await redis.setex(dedupe_key, 86400, "1")

    client_ip = request.client.host if request.client else "unknown"
    if not await check_rate_limit(f"rl:kiosk:{client_ip}:{device_identifier}", 60, 60):
        raise HTTPException(429, "Rate limit exceeded")

    await assert_channel_allowed(db, "kiosk")
    kiosk.last_seen = datetime.now(timezone.utc)

    frame_bytes = [await f.read() for f in files]
    if len(frame_bytes) < 3:
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="liveness_failed",
            display_message=MESSAGES["liveness_failed"],
        )

    liveness = await recognition_client.liveness_check(frame_bytes)
    if not liveness or not liveness.get("passed"):
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="liveness_failed",
            display_message=liveness.get("reason", MESSAGES["liveness_failed"]) if liveness else MESSAGES["liveness_failed"],
        )

    best_idx = liveness.get("best_frame_index", 0)
    embed_resp = await recognition_client.detect_and_embed(frame_bytes[min(best_idx, len(frame_bytes) - 1)])
    if not embed_resp or not embed_resp.get("embedding"):
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="face_not_recognized",
            display_message=MESSAGES["face_not_recognized"],
        )

    from app.services.match_settings import get_effective_match_threshold

    match_threshold = await get_effective_match_threshold(db)
    match = await find_best_match(db, embed_resp["embedding"])
    if match.ambiguous:
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="face_not_recognized",
            display_message="Ambiguous match — please try again",
            score=match.score,
        )
    employee_id = match.employee_id
    score = match.score
    if score < match_threshold or not employee_id:
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="face_not_recognized",
            display_message=MESSAGES["face_not_recognized"],
            score=score,
        )

    result = await db.execute(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.locations),
            selectinload(Employee.department),
            selectinload(Employee.job_role),
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="face_not_recognized",
            display_message=MESSAGES["face_not_recognized"],
        )

    active, inactive_code = check_employee_active(employee)
    if not active:
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code=inactive_code or "employee_disabled",
            display_message=MESSAGES["employee_disabled"],
            **build_employee_display(employee),
        )

    ok, policy_reason = await validate_kiosk_policy(db, employee, kiosk)
    if not ok:
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="device_not_authorized",
            display_message=policy_reason or MESSAGES["device_not_authorized"],
            **build_employee_display(employee),
        )

    valid, reason = await validate_attendance_context(
        db, request, employee, latitude, longitude, device_identifier, None
    )
    if not valid:
        log = AttendanceLog(
            employee_id=employee.id,
            kiosk_id=kiosk.id,
            device_id=device_identifier,
            recognition_score=score,
            event_type="rejected",
            latitude=latitude,
            longitude=longitude,
            rejection_reason=reason,
        )
        db.add(log)
        return KioskRecognizeResponse(
            matched=False,
            status="error",
            code="location_not_allowed",
            display_message=reason or MESSAGES["location_not_allowed"],
            score=score,
            **build_employee_display(employee),
        )

    event, level, code = await record_kiosk_attendance(db, employee, score, kiosk, action)
    now = datetime.now(timezone.utc)
    display = build_employee_display(employee)
    return KioskRecognizeResponse(
        matched=True,
        status=level,
        code=code,
        display_message=MESSAGES.get(code, f"Attendance recorded: {event}"),
        current_time=now,
        attendance_status=event,
        event=event,
        score=score,
        **display,
    )

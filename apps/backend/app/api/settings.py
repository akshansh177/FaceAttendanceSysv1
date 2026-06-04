from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.models import User, UserRole
from app.schemas.schemas import AttendanceSettingsResponse, AttendanceSettingsUpdate
from app.services.audit import log_audit
from app.services.cache_service import invalidate_entity_caches
from app.services.match_settings import MATCH_PRESETS, get_effective_match_threshold
from app.services.settings_service import get_org_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/attendance", response_model=AttendanceSettingsResponse)
async def get_attendance_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER))],
):
    s = await get_org_settings(db)
    effective = await get_effective_match_threshold(db)
    return AttendanceSettingsResponse(
        attendance_mode=s.attendance_mode,
        attendance_method=s.attendance_method,
        gps_enforcement_enabled=s.gps_enforcement_enabled,
        device_enforcement_enabled=s.device_enforcement_enabled,
        allowed_ip_cidrs=s.allowed_ip_cidrs or [],
        kiosk_checkout_after_checkout=s.kiosk_checkout_after_checkout,
        kiosk_screen_reset_seconds=s.kiosk_screen_reset_seconds,
        voice_feedback_enabled=s.voice_feedback_enabled,
        voice_language=s.voice_language,
        match_threshold_preset=s.match_threshold_preset,
        match_threshold=s.match_threshold,
        effective_match_threshold=effective,
    )


@router.put("/attendance", response_model=AttendanceSettingsResponse)
async def update_attendance_settings(
    body: AttendanceSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER))],
):
    s = await get_org_settings(db)
    data = body.model_dump(exclude_unset=True)
    if "match_threshold_preset" in data and data["match_threshold_preset"]:
        preset = data["match_threshold_preset"]
        if preset not in MATCH_PRESETS:
            from fastapi import HTTPException

            raise HTTPException(400, f"Invalid preset. Choose from: {', '.join(MATCH_PRESETS)}")
    for k, v in data.items():
        setattr(s, k, v)
    await log_audit(db, user.id, "settings.attendance.updated", "organization_settings", payload=data)
    await invalidate_entity_caches()
    s = await get_org_settings(db)
    effective = await get_effective_match_threshold(db)
    return AttendanceSettingsResponse(
        attendance_mode=s.attendance_mode,
        attendance_method=s.attendance_method,
        gps_enforcement_enabled=s.gps_enforcement_enabled,
        device_enforcement_enabled=s.device_enforcement_enabled,
        allowed_ip_cidrs=s.allowed_ip_cidrs or [],
        kiosk_checkout_after_checkout=s.kiosk_checkout_after_checkout,
        kiosk_screen_reset_seconds=s.kiosk_screen_reset_seconds,
        voice_feedback_enabled=s.voice_feedback_enabled,
        voice_language=s.voice_language,
        match_threshold_preset=s.match_threshold_preset,
        match_threshold=s.match_threshold,
        effective_match_threshold=effective,
    )

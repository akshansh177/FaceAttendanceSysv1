from __future__ import annotations

from fastapi import HTTPException

from app.models.models import AttendanceMethod
from app.services.settings_service import get_org_settings
from sqlalchemy.ext.asyncio import AsyncSession


async def assert_channel_allowed(db: AsyncSession, channel: str) -> None:
    """channel: kiosk | portal | recognize"""
    settings = await get_org_settings(db)
    method = settings.attendance_method

    allowed = {
        AttendanceMethod.KIOSK_ONLY: {"kiosk"},
        AttendanceMethod.PORTAL_ONLY: {"portal", "recognize"},
        AttendanceMethod.KIOSK_PORTAL: {"kiosk", "portal", "recognize"},
        AttendanceMethod.MOBILE_APP: set(),
        AttendanceMethod.ANY: {"kiosk", "portal", "recognize"},
    }.get(method, {"kiosk", "portal", "recognize"})

    if channel not in allowed:
        raise HTTPException(
            403,
            f"Attendance method '{method.value}' does not allow this channel",
        )

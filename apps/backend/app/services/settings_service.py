from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AttendanceMethod, AttendanceMode, OrganizationSettings


async def get_org_settings(db: AsyncSession) -> OrganizationSettings:
    result = await db.execute(select(OrganizationSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = OrganizationSettings(
            id=uuid.uuid4(),
            attendance_mode=AttendanceMode.FACE_ONLY,
            attendance_method=AttendanceMethod.KIOSK_PORTAL,
            gps_enforcement_enabled=False,
            device_enforcement_enabled=False,
            allowed_ip_cidrs=[],
            kiosk_checkout_after_checkout="ignore",
            kiosk_screen_reset_seconds=5,
            voice_feedback_enabled=True,
            voice_language="en",
        )
        db.add(settings)
        await db.flush()
    return settings

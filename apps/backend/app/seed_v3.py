"""Apply V3 seed data (kiosks, policies) on existing databases."""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import async_session
from app.models.models import (
    AttendanceKiosk,
    AttendanceMethod,
    AttendancePolicy,
    AttendanceMode,
    Department,
    Device,
    DeviceStatus,
    DeviceType,
    KioskStatus,
    OrganizationSettings,
    PolicyScopeType,
)
from app.services.kiosk_auth import generate_kiosk_api_key, hash_kiosk_key


async def seed_v3():
    async with async_session() as db:
        kiosk_q = await db.execute(select(AttendanceKiosk).limit(1))
        if kiosk_q.scalar_one_or_none():
            print("V3 seed already applied")
            return

        settings_q = await db.execute(select(OrganizationSettings).limit(1))
        settings = settings_q.scalar_one_or_none()
        if settings:
            settings.attendance_method = AttendanceMethod.KIOSK_PORTAL
            settings.kiosk_screen_reset_seconds = 5
            settings.voice_feedback_enabled = True

        dept_q = await db.execute(select(Department).where(Department.name == "Engineering"))
        dept = dept_q.scalar_one_or_none()
        loc = None
        from app.models.models import Location

        loc_q = await db.execute(select(Location).limit(1))
        loc = loc_q.scalar_one_or_none()

        raw_key = generate_kiosk_api_key()
        kiosk = AttendanceKiosk(
            name="Main Entrance",
            device_identifier="kiosk-main-gate",
            location_id=loc.id if loc else None,
            department_id=dept.id if dept else None,
            status=KioskStatus.ACTIVE,
            api_key_hash=hash_kiosk_key(raw_key),
        )
        db.add(kiosk)

        device_q = await db.execute(
            select(Device).where(Device.device_type == DeviceType.KIOSK, Device.status == DeviceStatus.APPROVED)
        )
        for d in device_q.scalars().all():
            key = generate_kiosk_api_key()
            db.add(
                AttendanceKiosk(
                    name=d.name,
                    device_identifier=d.device_id,
                    location_id=d.location_id,
                    status=KioskStatus.ACTIVE,
                    api_key_hash=hash_kiosk_key(key),
                )
            )

        if dept:
            db.add(
                AttendancePolicy(
                    name="Engineering — any kiosk",
                    scope_type=PolicyScopeType.DEPARTMENT,
                    scope_id=dept.id,
                    priority=10,
                    rules_json={"allowed_kiosk_ids": []},
                )
            )

        await db.commit()
        print("V3 seed complete. Sample kiosk device_identifier=kiosk-main-gate")
        print(f"API key (save now): {raw_key}")


if __name__ == "__main__":
    asyncio.run(seed_v3())

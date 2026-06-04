from __future__ import annotations

import asyncio
from datetime import date, time

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.models.models import (
    AttendanceMethod,
    AttendanceMode,
    AttendanceKiosk,
    Department,
    Device,
    DeviceStatus,
    DeviceType,
    Employee,
    EmployeeStatus,
    EmploymentType,
    JobRole,
    KioskStatus,
    Location,
    OrganizationSettings,
    Shift,
    ShiftType,
    User,
    UserRole,
)
from app.services.kiosk_auth import generate_kiosk_api_key, hash_kiosk_key


async def seed():
    async with async_session() as db:
        existing = await db.execute(select(User).where(User.email == "admin@company.com"))
        if existing.scalar_one_or_none():
            print("Seed already applied")
            return

        dept = Department(name="Engineering", description="Software and IT")
        db.add(dept)
        hr_dept = Department(name="HR", description="Human Resources")
        db.add(hr_dept)
        await db.flush()

        roles = [
            JobRole(name="Software Engineer", description="Development"),
            JobRole(name="HR Executive", description="HR operations"),
            JobRole(name="Manager", description="Team lead"),
        ]
        db.add_all(roles)
        await db.flush()

        loc_ho = Location(
            name="Head Office",
            address="Main Campus",
            latitude=28.6139,
            longitude=77.2090,
            radius_meters=200,
        )
        loc_wh = Location(name="Warehouse", address="Industrial Zone", latitude=28.5355, longitude=77.3910, radius_meters=300)
        db.add_all([loc_ho, loc_wh])
        await db.flush()

        shift = Shift(
            name="General",
            start_time=time(9, 0),
            end_time=time(18, 0),
            grace_minutes=15,
            shift_type=ShiftType.FIXED,
        )
        db.add(shift)
        await db.flush()

        emp = Employee(
            employee_code="EMP001",
            full_name="System Admin",
            email="admin.employee@company.com",
            department_id=dept.id,
            job_role_id=roles[2].id,
            shift_id=shift.id,
            employment_type=EmploymentType.FULL_TIME,
            joining_date=date(2024, 1, 1),
            status=EmployeeStatus.ACTIVE,
        )
        db.add(emp)
        await db.flush()
        from app.models.models import employee_locations
        from sqlalchemy import insert
        await db.execute(
            insert(employee_locations).values(employee_id=emp.id, location_id=loc_ho.id)
        )

        admin = User(
            email="admin@company.com",
            password_hash=hash_password("Admin123!"),
            role=UserRole.SUPER_ADMIN,
            employee_id=emp.id,
        )
        hr_user = User(
            email="hr@company.com",
            password_hash=hash_password("Hr123456!"),
            role=UserRole.HR_MANAGER,
        )
        db.add_all([admin, hr_user])

        settings = OrganizationSettings(
            attendance_mode=AttendanceMode.FACE_ONLY,
            attendance_method=AttendanceMethod.KIOSK_PORTAL,
            gps_enforcement_enabled=False,
            device_enforcement_enabled=False,
            allowed_ip_cidrs=["127.0.0.0/8", "10.0.0.0/8"],
            kiosk_checkout_after_checkout="ignore",
            kiosk_screen_reset_seconds=5,
            voice_feedback_enabled=True,
            voice_language="en",
        )
        db.add(settings)

        device = Device(
            device_id="kiosk-001",
            name="Main Entrance Kiosk",
            device_type=DeviceType.KIOSK,
            location_id=loc_ho.id,
            status=DeviceStatus.APPROVED,
        )
        db.add(device)

        kiosk_key = generate_kiosk_api_key()
        kiosk = AttendanceKiosk(
            name="Main Entrance",
            device_identifier="kiosk-main-gate",
            location_id=loc_ho.id,
            department_id=dept.id,
            status=KioskStatus.ACTIVE,
            api_key_hash=hash_kiosk_key(kiosk_key),
        )
        db.add(kiosk)

        await db.commit()
        print("Seed complete: admin@company.com / Admin123!")
        print(f"Kiosk device_identifier=kiosk-main-gate api_key={kiosk_key}")


if __name__ == "__main__":
    asyncio.run(seed())

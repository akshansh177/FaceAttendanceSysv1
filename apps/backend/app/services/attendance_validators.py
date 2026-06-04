from __future__ import annotations

import ipaddress
import math
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import AttendanceMode, Device, DeviceStatus, Employee
from app.services.settings_service import get_org_settings


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


async def validate_attendance_context(
    db: AsyncSession,
    request: Request,
    employee: Employee,
    latitude: float | None,
    longitude: float | None,
    device_id: str | None,
    device_mac: str | None,
) -> tuple[bool, str | None]:
    settings = await get_org_settings(db)
    mode = settings.attendance_mode

    if mode in (AttendanceMode.FACE_GPS, AttendanceMode.FACE_GPS_DEVICE) or settings.gps_enforcement_enabled:
        if latitude is None or longitude is None:
            return False, "GPS coordinates required"
        result = await db.execute(
            select(Employee)
            .where(Employee.id == employee.id)
            .options(selectinload(Employee.locations))
        )
        emp = result.scalar_one()
        if not emp.locations:
            return False, "No locations assigned to employee"
        in_range = False
        for loc in emp.locations:
            if not loc.is_active:
                continue
            dist = haversine_meters(latitude, longitude, loc.latitude, loc.longitude)
            if dist <= loc.radius_meters:
                in_range = True
                break
        if not in_range:
            return False, "Outside allowed location radius"

    if mode == AttendanceMode.FACE_NETWORK:
        cidrs = settings.allowed_ip_cidrs or []
        if not cidrs:
            return False, "Office network not configured"
        ip = client_ip(request)
        try:
            addr = ipaddress.ip_address(ip)
            allowed = any(addr in ipaddress.ip_network(c, strict=False) for c in cidrs)
        except ValueError:
            allowed = False
        if not allowed:
            return False, f"IP {ip} not on office network"

    if mode == AttendanceMode.FACE_GPS_DEVICE or settings.device_enforcement_enabled:
        lookup = device_id or device_mac
        if not lookup:
            return False, "Registered device required"
        q = select(Device).where(Device.status == DeviceStatus.APPROVED)
        if device_id:
            q = q.where(Device.device_id == device_id)
        else:
            q = q.where(Device.mac_address == device_mac)
        result = await db.execute(q)
        if not result.scalar_one_or_none():
            return False, "Device not approved"

    return True, None

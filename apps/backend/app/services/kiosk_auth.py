from __future__ import annotations

import secrets

from fastapi import Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.models import AttendanceKiosk, KioskStatus


def generate_kiosk_api_key() -> str:
    return f"kiosk_{secrets.token_urlsafe(32)}"


async def authenticate_kiosk(
    db: AsyncSession,
    device_identifier: str,
    x_kiosk_key: str | None,
) -> AttendanceKiosk:
    if not x_kiosk_key or not device_identifier:
        raise HTTPException(401, "Kiosk credentials required")

    result = await db.execute(
        select(AttendanceKiosk)
        .where(AttendanceKiosk.device_identifier == device_identifier)
        .options(selectinload(AttendanceKiosk.location))
    )
    kiosk = result.scalar_one_or_none()
    if not kiosk:
        raise HTTPException(401, "Unknown kiosk device")
    if kiosk.status != KioskStatus.ACTIVE:
        raise HTTPException(403, "Kiosk is disabled")
    if not verify_password(x_kiosk_key, kiosk.api_key_hash):
        raise HTTPException(401, "Invalid kiosk API key")
    return kiosk


def hash_kiosk_key(raw_key: str) -> str:
    return hash_password(raw_key)

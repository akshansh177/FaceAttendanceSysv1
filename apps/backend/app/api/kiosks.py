from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import AttendanceKiosk, User, kiosk_employee_access
from app.schemas.schemas import KioskCreate, KioskCreateResponse, KioskResponse, KioskUpdate, MessageResponse
from app.services.audit import log_audit
from app.services.kiosk_auth import generate_kiosk_api_key, hash_kiosk_key

router = APIRouter(prefix="/api/kiosks", tags=["kiosks"])


def _to_response(k: AttendanceKiosk) -> KioskResponse:
    online = False
    if k.last_seen:
        last = k.last_seen
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        online = last >= datetime.now(timezone.utc) - timedelta(minutes=5)
    return KioskResponse(
        id=k.id,
        name=k.name,
        device_identifier=k.device_identifier,
        location_id=k.location_id,
        department_id=k.department_id,
        status=k.status,
        last_seen=k.last_seen,
        is_online=online,
        created_at=k.created_at,
        employee_ids=[e.id for e in k.allowed_employees] if k.allowed_employees else [],
    )


async def _reload_kiosk(db: AsyncSession, kiosk_id: UUID) -> AttendanceKiosk:
    result = await db.execute(
        select(AttendanceKiosk)
        .where(AttendanceKiosk.id == kiosk_id)
        .options(selectinload(AttendanceKiosk.allowed_employees))
    )
    return result.scalar_one()


async def _set_kiosk_employees(db: AsyncSession, kiosk: AttendanceKiosk, employee_ids: list[UUID]) -> None:
    await db.execute(delete(kiosk_employee_access).where(kiosk_employee_access.c.kiosk_id == kiosk.id))
    if employee_ids:
        await db.execute(
            insert(kiosk_employee_access),
            [{"kiosk_id": kiosk.id, "employee_id": eid} for eid in employee_ids],
        )


@router.get("", response_model=list[KioskResponse])
async def list_kiosks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(
        select(AttendanceKiosk).options(selectinload(AttendanceKiosk.allowed_employees)).order_by(AttendanceKiosk.name)
    )
    return [_to_response(k) for k in result.scalars().all()]


@router.post("", response_model=KioskCreateResponse, status_code=201)
async def create_kiosk(
    body: KioskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    raw_key = generate_kiosk_api_key()
    kiosk = AttendanceKiosk(
        name=body.name,
        device_identifier=body.device_identifier,
        location_id=body.location_id,
        department_id=body.department_id,
        status=body.status,
        api_key_hash=hash_kiosk_key(raw_key),
    )
    db.add(kiosk)
    await db.flush()
    await _set_kiosk_employees(db, kiosk, body.employee_ids)
    await log_audit(db, user.id, "kiosk.created", "attendance_kiosks", payload={"name": body.name})
    kiosk = await _reload_kiosk(db, kiosk.id)
    resp = _to_response(kiosk)
    return KioskCreateResponse(**resp.model_dump(), api_key=raw_key)


@router.put("/{kiosk_id}", response_model=KioskResponse)
async def update_kiosk(
    kiosk_id: UUID,
    body: KioskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(
        select(AttendanceKiosk)
        .where(AttendanceKiosk.id == kiosk_id)
        .options(selectinload(AttendanceKiosk.allowed_employees))
    )
    kiosk = result.scalar_one_or_none()
    if not kiosk:
        raise HTTPException(404, "Kiosk not found")
    for k, v in body.model_dump(exclude_unset=True, exclude={"employee_ids"}).items():
        setattr(kiosk, k, v)
    if body.employee_ids is not None:
        await _set_kiosk_employees(db, kiosk, body.employee_ids)
    await log_audit(db, user.id, "kiosk.updated", "attendance_kiosks", payload={"id": str(kiosk_id)})
    kiosk = await _reload_kiosk(db, kiosk_id)
    return _to_response(kiosk)


@router.delete("/{kiosk_id}", response_model=MessageResponse)
async def delete_kiosk(
    kiosk_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(AttendanceKiosk).where(AttendanceKiosk.id == kiosk_id))
    kiosk = result.scalar_one_or_none()
    if not kiosk:
        raise HTTPException(404, "Kiosk not found")
    await db.delete(kiosk)
    await log_audit(db, user.id, "kiosk.deleted", "attendance_kiosks", payload={"id": str(kiosk_id)})
    return MessageResponse(message="Kiosk deleted")

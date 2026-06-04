from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import Device, User
from app.schemas.schemas import DeviceCreate, DeviceResponse, DeviceUpdate, MessageResponse
from app.services.audit import log_audit

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceResponse])
async def list_devices(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(require_roles(*HR_ROLES))]):
    result = await db.execute(select(Device).order_by(Device.name))
    return result.scalars().all()


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_device(
    body: DeviceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    device = Device(**body.model_dump())
    db.add(device)
    await db.flush()
    await log_audit(db, user.id, "device.created", "devices", payload={"device_id": body.device_id})
    await db.refresh(device)
    return device


@router.put("/{device_pk}", response_model=DeviceResponse)
async def update_device(
    device_pk: UUID,
    body: DeviceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Device).where(Device.id == device_pk))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(device, k, v)
    await log_audit(db, user.id, "device.updated", "devices", payload={"id": str(device_pk)})
    await db.refresh(device)
    return device


@router.delete("/{device_pk}", response_model=MessageResponse)
async def delete_device(
    device_pk: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Device).where(Device.id == device_pk))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")
    await db.delete(device)
    await log_audit(db, user.id, "device.deleted", "devices", payload={"id": str(device_pk)})
    return MessageResponse(message="Device deleted")

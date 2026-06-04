from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import Shift, User
from app.schemas.schemas import MessageResponse, ShiftCreate, ShiftResponse, ShiftUpdate
from app.services.cache_service import invalidate_entity_caches

router = APIRouter(prefix="/api/shifts", tags=["shifts"])


@router.get("", response_model=list[ShiftResponse])
async def list_shifts(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(require_roles(*HR_ROLES))]):
    result = await db.execute(select(Shift).order_by(Shift.name))
    return result.scalars().all()


@router.post("", response_model=ShiftResponse, status_code=201)
async def create_shift(
    body: ShiftCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    shift = Shift(**body.model_dump())
    db.add(shift)
    await db.flush()
    await db.refresh(shift)
    await invalidate_entity_caches()
    return shift


@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: UUID,
    body: ShiftUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(404, "Shift not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(shift, k, v)
    await db.flush()
    await db.refresh(shift)
    await invalidate_entity_caches()
    return shift


@router.delete("/{shift_id}", response_model=MessageResponse)
async def delete_shift(
    shift_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(404, "Shift not found")
    await db.delete(shift)
    await invalidate_entity_caches()
    return MessageResponse(message="Shift deleted")

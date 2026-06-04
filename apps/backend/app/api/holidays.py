from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import Holiday, User
from app.schemas.schemas import HolidayCreate, HolidayResponse, MessageResponse

router = APIRouter(prefix="/api/holidays", tags=["holidays"])


@router.get("", response_model=list[HolidayResponse])
async def list_holidays(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(require_roles(*HR_ROLES))]):
    result = await db.execute(select(Holiday).order_by(Holiday.date))
    return result.scalars().all()


@router.post("", response_model=HolidayResponse, status_code=201)
async def create_holiday(
    body: HolidayCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    h = Holiday(**body.model_dump())
    db.add(h)
    await db.flush()
    await db.refresh(h)
    return h


@router.delete("/{holiday_id}", response_model=MessageResponse)
async def delete_holiday(
    holiday_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    h = result.scalar_one_or_none()
    if not h:
        raise HTTPException(404, "Holiday not found")
    await db.delete(h)
    return MessageResponse(message="Holiday deleted")

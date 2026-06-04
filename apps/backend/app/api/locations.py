from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import Location, User
from app.schemas.schemas import LocationCreate, LocationResponse, MessageResponse
from app.services.audit import log_audit

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
async def list_locations(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(require_roles(*HR_ROLES))]):
    result = await db.execute(select(Location).order_by(Location.name))
    return result.scalars().all()


@router.post("", response_model=LocationResponse, status_code=201)
async def create_location(
    body: LocationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    loc = Location(**body.model_dump())
    db.add(loc)
    await db.flush()
    await log_audit(db, user.id, "location.created", "locations", payload={"name": body.name})
    await db.refresh(loc)
    return loc


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    body: LocationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(404, "Location not found")
    for k, v in body.model_dump().items():
        setattr(loc, k, v)
    await db.refresh(loc)
    return loc


@router.delete("/{location_id}", response_model=MessageResponse)
async def delete_location(
    location_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(404, "Location not found")
    await db.delete(loc)
    return MessageResponse(message="Location deleted")

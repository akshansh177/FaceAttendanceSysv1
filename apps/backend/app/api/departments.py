from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import Department, User
from app.schemas.schemas import DepartmentCreate, DepartmentResponse, MessageResponse
from app.services.cache_service import get_or_load_json, invalidate_entity_caches

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(require_roles(*HR_ROLES))]):
    async def _load():
        result = await db.execute(select(Department).order_by(Department.name))
        return [DepartmentResponse.model_validate(d).model_dump(mode="json") for d in result.scalars().all()]

    data = await get_or_load_json("cache:departments:list", _load)
    return [DepartmentResponse(**row) for row in data]


@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    body: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    dept = Department(name=body.name)
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    await invalidate_entity_caches()
    return dept


@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: UUID,
    body: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(404, "Department not found")
    dept.name = body.name
    await db.flush()
    await db.refresh(dept)
    await invalidate_entity_caches()
    return dept


@router.delete("/{dept_id}", response_model=MessageResponse)
async def delete_department(
    dept_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(404, "Department not found")
    await db.delete(dept)
    await invalidate_entity_caches()
    return MessageResponse(message="Department deleted")

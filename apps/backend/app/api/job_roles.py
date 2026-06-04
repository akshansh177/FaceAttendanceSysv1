from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import JobRole, User
from app.schemas.schemas import JobRoleCreate, JobRoleResponse, MessageResponse
from app.services.audit import log_audit

router = APIRouter(prefix="/api/job-roles", tags=["job-roles"])


@router.get("", response_model=list[JobRoleResponse])
async def list_job_roles(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(require_roles(*HR_ROLES))]):
    result = await db.execute(select(JobRole).order_by(JobRole.name))
    return result.scalars().all()


@router.post("", response_model=JobRoleResponse, status_code=201)
async def create_job_role(
    body: JobRoleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    role = JobRole(**body.model_dump())
    db.add(role)
    await db.flush()
    await log_audit(db, user.id, "job_role.created", "job_roles", payload={"name": body.name})
    await db.refresh(role)
    return role


@router.put("/{role_id}", response_model=JobRoleResponse)
async def update_job_role(
    role_id: UUID,
    body: JobRoleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(JobRole).where(JobRole.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Job role not found")
    for k, v in body.model_dump().items():
        setattr(role, k, v)
    await log_audit(db, user.id, "job_role.updated", "job_roles", payload={"id": str(role_id)})
    await db.refresh(role)
    return role


@router.delete("/{role_id}", response_model=MessageResponse)
async def delete_job_role(
    role_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(JobRole).where(JobRole.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Job role not found")
    await db.delete(role)
    await log_audit(db, user.id, "job_role.deleted", "job_roles", payload={"id": str(role_id)})
    return MessageResponse(message="Job role deleted")

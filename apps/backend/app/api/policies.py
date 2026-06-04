from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import AttendancePolicy, User
from app.schemas.schemas import MessageResponse, PolicyCreate, PolicyResponse
from app.services.audit import log_audit
from app.services.policy_service import invalidate_policy_cache, warm_policy_cache

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(AttendancePolicy).order_by(AttendancePolicy.priority))
    return result.scalars().all()


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    body: PolicyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    policy = AttendancePolicy(**body.model_dump())
    db.add(policy)
    await db.flush()
    await log_audit(db, user.id, "policy.created", "attendance_policies", payload={"name": body.name})
    await db.refresh(policy)
    await invalidate_policy_cache()
    await warm_policy_cache(db)
    return policy


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    body: PolicyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(AttendancePolicy).where(AttendancePolicy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(404, "Policy not found")
    for k, v in body.model_dump().items():
        setattr(policy, k, v)
    await log_audit(db, user.id, "policy.updated", "attendance_policies")
    await db.refresh(policy)
    await invalidate_policy_cache()
    await warm_policy_cache(db)
    return policy


@router.delete("/{policy_id}", response_model=MessageResponse)
async def delete_policy(
    policy_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(AttendancePolicy).where(AttendancePolicy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(404, "Policy not found")
    await db.delete(policy)
    await log_audit(db, user.id, "policy.deleted", "attendance_policies")
    await invalidate_policy_cache()
    await warm_policy_cache(db)
    return MessageResponse(message="Policy deleted")

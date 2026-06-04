from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import HR_ROLES, get_current_user, require_roles
from app.models.models import LeaveRequest, User, UserRole
from app.schemas.schemas import LeaveCreate, LeaveResponse, LeaveUpdate, MessageResponse

router = APIRouter(prefix="/api/leaves", tags=["leaves"])


@router.get("", response_model=list[LeaveResponse])
async def list_leaves(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    q = select(LeaveRequest)
    if user.role == UserRole.EMPLOYEE and user.employee_id:
        q = q.where(LeaveRequest.employee_id == user.employee_id)
    result = await db.execute(q.order_by(LeaveRequest.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=LeaveResponse, status_code=201)
async def create_leave(
    body: LeaveCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role == UserRole.EMPLOYEE:
        if not user.employee_id or body.employee_id != user.employee_id:
            raise HTTPException(403, "Can only create leave for yourself")
    leave = LeaveRequest(**body.model_dump())
    db.add(leave)
    await db.flush()
    await db.refresh(leave)
    return leave


@router.patch("/{leave_id}", response_model=LeaveResponse)
async def update_leave(
    leave_id: UUID,
    body: LeaveUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(LeaveRequest).where(LeaveRequest.id == leave_id))
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(404, "Leave not found")
    leave.status = body.status
    await db.flush()
    await db.refresh(leave)
    return leave

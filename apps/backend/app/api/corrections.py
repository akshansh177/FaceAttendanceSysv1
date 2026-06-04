from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import HR_ROLES, MANAGER_ROLES, get_current_user, require_roles
from app.models.models import (
    AttendanceCorrection,
    AttendanceSummary,
    CorrectionStatus,
    Employee,
    User,
    UserRole,
    WorkflowStatus,
)
from app.schemas.schemas import CorrectionCreate, CorrectionResponse, MessageResponse
from app.services.attendance_engine import process_daily_summary
from app.services.audit import log_audit
from app.services.notifications import notify_correction_status

router = APIRouter(prefix="/api/attendance/corrections", tags=["corrections"])


@router.get("", response_model=list[CorrectionResponse])
async def list_corrections(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status: CorrectionStatus | None = None,
):
    q = select(AttendanceCorrection).order_by(AttendanceCorrection.created_at.desc())
    if user.role == UserRole.EMPLOYEE and user.employee_id:
        q = q.where(AttendanceCorrection.employee_id == user.employee_id)
    elif user.role == UserRole.TEAM_MANAGER and user.employee_id:
        team = await db.execute(select(Employee.id).where(Employee.manager_id == user.employee_id))
        ids = [r[0] for r in team.all()]
        q = q.where(AttendanceCorrection.employee_id.in_(ids)) if ids else q.where(False)
    if status:
        q = q.where(AttendanceCorrection.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=CorrectionResponse, status_code=201)
async def create_correction(
    body: CorrectionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if not user.employee_id:
        raise HTTPException(400, "Employee profile required")
    corr = AttendanceCorrection(
        employee_id=user.employee_id,
        date=body.date,
        requested_check_in=body.requested_check_in,
        requested_check_out=body.requested_check_out,
        reason=body.reason,
    )
    db.add(corr)
    await db.flush()
    await log_audit(db, user.id, "attendance.correction.requested", "attendance_corrections")
    await db.refresh(corr)
    return corr


@router.patch("/{correction_id}/approve", response_model=CorrectionResponse)
async def approve_correction(
    correction_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(AttendanceCorrection).where(AttendanceCorrection.id == correction_id))
    corr = result.scalar_one_or_none()
    if not corr:
        raise HTTPException(404, "Correction not found")

    if user.role == UserRole.TEAM_MANAGER and corr.status == CorrectionStatus.PENDING_MANAGER:
        corr.status = CorrectionStatus.PENDING_HR
        corr.manager_approved_by = user.id
        from datetime import datetime, timezone
        corr.manager_approved_at = datetime.now(timezone.utc)
    elif user.role in (UserRole.HR_MANAGER, UserRole.SUPER_ADMIN) and corr.status == CorrectionStatus.PENDING_HR:
        corr.status = CorrectionStatus.APPROVED
        corr.hr_approved_by = user.id
        from datetime import datetime, timezone
        corr.hr_approved_at = datetime.now(timezone.utc)
        summary_result = await db.execute(
            select(AttendanceSummary).where(
                and_(AttendanceSummary.employee_id == corr.employee_id, AttendanceSummary.date == corr.date)
            )
        )
        summary = summary_result.scalar_one_or_none()
        if not summary:
            summary = AttendanceSummary(employee_id=corr.employee_id, date=corr.date)
            db.add(summary)
        if corr.requested_check_in:
            summary.check_in = corr.requested_check_in
        if corr.requested_check_out:
            summary.check_out = corr.requested_check_out
        emp_result = await db.execute(
            select(Employee).where(Employee.id == corr.employee_id).options(selectinload(Employee.shift))
        )
        emp = emp_result.scalar_one()
        await process_daily_summary(db, emp, corr.date)
        await log_audit(db, user.id, "attendance.correction.approved", "attendance_corrections", payload={"id": str(correction_id)})
        emp_user = await db.execute(select(User).where(User.employee_id == corr.employee_id))
        u = emp_user.scalar_one_or_none()
        if u and u.email_notifications:
            notify_correction_status(u.email, "approved", str(corr.date))
    else:
        raise HTTPException(403, "Invalid approval state for your role")

    await db.refresh(corr)
    return corr


@router.patch("/{correction_id}/reject", response_model=CorrectionResponse)
async def reject_correction(
    correction_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.TEAM_MANAGER))],
):
    result = await db.execute(select(AttendanceCorrection).where(AttendanceCorrection.id == correction_id))
    corr = result.scalar_one_or_none()
    if not corr:
        raise HTTPException(404, "Correction not found")
    corr.status = CorrectionStatus.REJECTED
    await log_audit(db, user.id, "attendance.correction.rejected", "attendance_corrections")
    emp_user = await db.execute(select(User).where(User.employee_id == corr.employee_id))
    u = emp_user.scalar_one_or_none()
    if u and u.email_notifications:
        notify_correction_status(u.email, "rejected", str(corr.date))
    await db.refresh(corr)
    return corr

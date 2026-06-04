from __future__ import annotations

import csv
import io
from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.models.models import AttendanceSummary, Employee, User
from app.schemas.schemas import (
    CalendarDay,
    EmployeeDashboard,
    EmployeeProfileResponse,
    EmployeeProfileUpdate,
    MessageResponse,
    PasswordChangeRequest,
    ShiftInfoResponse,
)
from app.services.dashboard import get_employee_dashboard

router = APIRouter(prefix="/api/me", tags=["me"])


async def _require_employee(db: AsyncSession, user: User) -> Employee:
    if not user.employee_id:
        raise HTTPException(400, "Employee profile required")
    result = await db.execute(
        select(Employee)
        .where(Employee.id == user.employee_id)
        .options(
            selectinload(Employee.department),
            selectinload(Employee.job_role),
            selectinload(Employee.shift),
        )
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    return emp


@router.get("/profile", response_model=EmployeeProfileResponse)
async def get_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    emp = await _require_employee(db, user)
    return EmployeeProfileResponse(
        id=emp.id,
        employee_code=emp.employee_code,
        full_name=emp.full_name,
        email=emp.email,
        phone=emp.phone,
        department=emp.department.name if emp.department else None,
        job_role=emp.job_role.name if emp.job_role else None,
        shift_name=emp.shift.name if emp.shift else None,
        profile_photo_path=emp.profile_photo_path,
    )


@router.put("/profile", response_model=EmployeeProfileResponse)
async def update_profile(
    body: EmployeeProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    emp = await _require_employee(db, user)
    if body.phone is not None:
        emp.phone = body.phone
    return await get_profile(db, user)


@router.get("/dashboard", response_model=EmployeeDashboard)
async def my_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if not user.employee_id:
        return EmployeeDashboard(
            today_status=None,
            workflow_status=None,
            monthly_present=0,
            monthly_absent=0,
        )
    return await get_employee_dashboard(db, user.employee_id)


@router.get("/shift", response_model=Optional[ShiftInfoResponse])
async def my_shift(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    emp = await _require_employee(db, user)
    if not emp.shift:
        return None
    return ShiftInfoResponse(
        name=emp.shift.name,
        start_time=emp.shift.start_time,
        end_time=emp.shift.end_time,
        grace_minutes=emp.shift.grace_minutes,
        shift_type=emp.shift.shift_type,
    )


@router.get("/attendance/calendar", response_model=list[CalendarDay])
async def attendance_calendar(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
):
    if not user.employee_id:
        return []
    year, mon = map(int, month.split("-"))
    start = date(year, mon, 1)
    if mon == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, mon + 1, 1)
    result = await db.execute(
        select(AttendanceSummary).where(
            and_(
                AttendanceSummary.employee_id == user.employee_id,
                AttendanceSummary.date >= start,
                AttendanceSummary.date < end,
            )
        )
    )
    return [
        CalendarDay(
            date=s.date,
            status=s.status.value,
            check_in=s.check_in,
            check_out=s.check_out,
        )
        for s in result.scalars().all()
    ]


@router.get("/attendance/export")
async def export_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    from_date: date | None = None,
    to_date: date | None = None,
):
    if not user.employee_id:
        raise HTTPException(400, "Employee profile required")
    q = select(AttendanceSummary).where(AttendanceSummary.employee_id == user.employee_id)
    if from_date:
        q = q.where(AttendanceSummary.date >= from_date)
    if to_date:
        q = q.where(AttendanceSummary.date <= to_date)
    result = await db.execute(q.order_by(AttendanceSummary.date.desc()))
    rows = result.scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "check_in", "check_out", "status", "late_minutes", "overtime_minutes"])
    for r in rows:
        writer.writerow([
            r.date.isoformat(),
            r.check_in.isoformat() if r.check_in else "",
            r.check_out.isoformat() if r.check_out else "",
            r.status.value,
            r.late_minutes,
            r.overtime_minutes,
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance.csv"},
    )

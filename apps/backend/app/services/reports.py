from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import AttendanceStatus, AttendanceSummary, Department, Employee
from app.schemas.schemas import ReportRow


async def _rows_from_summaries(
    db: AsyncSession,
    summaries: list[AttendanceSummary],
) -> list[ReportRow]:
    rows: list[ReportRow] = []
    for s in summaries:
        emp = s.employee
        dept_name = emp.department.name if emp.department else None
        rows.append(
            ReportRow(
                employee_code=emp.employee_code,
                full_name=emp.full_name,
                department=dept_name,
                attendance_date=s.date,
                check_in=s.check_in.isoformat() if s.check_in else None,
                check_out=s.check_out.isoformat() if s.check_out else None,
                status=s.status.value,
                late_minutes=s.late_minutes,
                overtime_minutes=s.overtime_minutes,
            )
        )
    return rows


async def daily_report(db: AsyncSession, report_date: date, department_id=None) -> list[ReportRow]:
    q = (
        select(AttendanceSummary)
        .where(AttendanceSummary.date == report_date)
        .options(
            selectinload(AttendanceSummary.employee).selectinload(Employee.department)
        )
    )
    result = await db.execute(q)
    summaries = list(result.scalars().all())
    if department_id:
        summaries = [s for s in summaries if s.employee.department_id == department_id]
    summaries.sort(key=lambda s: (s.employee.full_name or "", s.employee.employee_code or ""))
    return await _rows_from_summaries(db, summaries)


async def filtered_report(
    db: AsyncSession,
    start: date,
    end: date,
    status_filter: AttendanceStatus | None = None,
    department_id=None,
) -> list[ReportRow]:
    q = (
        select(AttendanceSummary)
        .where(and_(AttendanceSummary.date >= start, AttendanceSummary.date <= end))
        .options(selectinload(AttendanceSummary.employee).selectinload(Employee.department))
    )
    if status_filter:
        q = q.where(AttendanceSummary.status == status_filter)
    result = await db.execute(q)
    summaries = list(result.scalars().all())
    if department_id:
        summaries = [s for s in summaries if s.employee.department_id == department_id]
    summaries.sort(key=lambda s: (s.date, s.employee.full_name or ""))
    return await _rows_from_summaries(db, summaries)


async def weekly_report(
    db: AsyncSession, week_start: date, department_id=None
) -> list[ReportRow]:
    return await filtered_report(db, week_start, week_start + timedelta(days=6), department_id=department_id)


async def monthly_report(
    db: AsyncSession, year: int, month: int, department_id=None
) -> list[ReportRow]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return await filtered_report(db, start, end, department_id=department_id)

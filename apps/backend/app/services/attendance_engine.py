from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.models import (
    AttendanceStatus,
    AttendanceSummary,
    Employee,
    EmployeeStatus,
    Holiday,
    HolidayScope,
    LeaveRequest,
    LeaveStatus,
    Shift,
    WorkflowStatus,
)


def _combine_datetime(d: date, t: time) -> datetime:
    return datetime.combine(d, t).replace(tzinfo=timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    """MySQL often returns naive datetimes; normalize for comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _minutes_between(start: datetime, end: datetime) -> int:
    start = _as_utc(start) or start
    end = _as_utc(end) or end
    return max(0, int((end - start).total_seconds() / 60))


async def process_daily_summary(
    db: AsyncSession, employee: Employee, summary_date: date
) -> AttendanceSummary:
    result = await db.execute(
        select(AttendanceSummary).where(
            and_(
                AttendanceSummary.employee_id == employee.id,
                AttendanceSummary.date == summary_date,
            )
        )
    )
    summary = result.scalar_one_or_none()
    if not summary:
        summary = AttendanceSummary(employee_id=employee.id, date=summary_date)
        db.add(summary)

    weekday = summary_date.weekday()
    if weekday >= 5:
        summary.status = AttendanceStatus.WEEKEND
        summary.late_minutes = 0
        summary.overtime_minutes = 0
        return summary

    holiday_q = await db.execute(
        select(Holiday).where(
            and_(
                Holiday.date == summary_date,
                (Holiday.scope == HolidayScope.GLOBAL)
                | (Holiday.department_id == employee.department_id),
            )
        )
    )
    if holiday_q.scalar_one_or_none():
        summary.status = AttendanceStatus.HOLIDAY
        return summary

    leave_q = await db.execute(
        select(LeaveRequest).where(
            and_(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.status == LeaveStatus.APPROVED,
                LeaveRequest.start_date <= summary_date,
                LeaveRequest.end_date >= summary_date,
            )
        )
    )
    if leave_q.scalar_one_or_none():
        summary.status = AttendanceStatus.ON_LEAVE
        return summary

    check_in = _as_utc(summary.check_in)
    check_out = _as_utc(summary.check_out)

    if not check_in:
        summary.status = AttendanceStatus.ABSENT
        summary.late_minutes = 0
        summary.overtime_minutes = 0
        return summary

    settings = get_settings()
    shift: Shift | None = employee.shift
    late_minutes = 0
    overtime_minutes = 0
    status = AttendanceStatus.PRESENT

    if shift:
        shift_start = _combine_datetime(summary_date, shift.start_time)
        shift_end = _combine_datetime(summary_date, shift.end_time)
        if shift.end_time <= shift.start_time:
            shift_end += timedelta(days=1)

        grace = timedelta(minutes=shift.grace_minutes)
        if check_in > shift_start + grace:
            late_minutes = _minutes_between(shift_start + grace, check_in)
            status = AttendanceStatus.LATE

        if check_out:
            early_threshold = shift_end - grace
            if check_out < early_threshold:
                status = AttendanceStatus.EARLY_LEAVE

            ot_threshold = shift_end + timedelta(minutes=settings.overtime_threshold_minutes)
            if check_out > ot_threshold:
                overtime_minutes = _minutes_between(ot_threshold, check_out)
                if overtime_minutes > 0:
                    status = AttendanceStatus.OVERTIME

            worked_hours = (check_out - check_in).total_seconds() / 3600
            if worked_hours < settings.half_day_hours:
                status = AttendanceStatus.HALF_DAY

    summary.late_minutes = late_minutes
    summary.overtime_minutes = overtime_minutes
    summary.status = status

    if check_in and not check_out:
        summary.workflow_status = WorkflowStatus.CHECKED_IN
        summary.worked_minutes = 0
    elif check_in and check_out:
        summary.workflow_status = WorkflowStatus.CHECKED_OUT
        summary.worked_minutes = _minutes_between(check_in, check_out)
    else:
        summary.workflow_status = None
        summary.worked_minutes = 0

    if shift:
        shift_start = _combine_datetime(summary_date, shift.start_time)
        shift_end = _combine_datetime(summary_date, shift.end_time)
        if shift.end_time <= shift.start_time:
            shift_end += timedelta(days=1)
        summary.expected_minutes = _minutes_between(shift_start, shift_end)
    else:
        summary.expected_minutes = 480

    return summary


async def mark_missing_checkouts(db: AsyncSession, target_date: date | None = None) -> int:
    d = target_date or date.today()
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AttendanceSummary)
        .where(AttendanceSummary.date == d)
        .options(selectinload(AttendanceSummary.employee).selectinload(Employee.shift))
    )
    count = 0
    for summary in result.scalars().all():
        if summary.check_in and not summary.check_out and summary.employee.shift:
            shift_end = _combine_datetime(d, summary.employee.shift.end_time)
            if now > shift_end + timedelta(hours=2):
                summary.workflow_status = WorkflowStatus.MISSING_CHECKOUT
                count += 1
    return count


async def recompute_all_summaries(db: AsyncSession, target_date: date | None = None) -> int:
    d = target_date or date.today()
    result = await db.execute(
        select(Employee)
        .where(Employee.status == EmployeeStatus.ACTIVE)
        .options(selectinload(Employee.shift))
    )
    employees = result.scalars().all()
    count = 0
    for emp in employees:
        await process_daily_summary(db, emp, d)
        count += 1
    return count

from __future__ import annotations

import json
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.redis_client import get_redis
from app.models.models import (
    AttendanceStatus,
    AttendanceSummary,
    Employee,
    EmployeeStatus,
    UserRole,
    WorkflowStatus,
)
from app.schemas.schemas import DashboardMetrics, DashboardTrends, EmployeeDashboard


async def _summaries_today(db: AsyncSession) -> list[AttendanceSummary]:
    today = date.today()
    result = await db.execute(
        select(AttendanceSummary)
        .where(AttendanceSummary.date == today)
        .options(selectinload(AttendanceSummary.employee).selectinload(Employee.department))
    )
    return list(result.scalars().all())


async def get_metrics(db: AsyncSession, use_cache: bool = True) -> DashboardMetrics:
    redis = await get_redis()
    cache_key = f"dashboard:metrics:{date.today().isoformat()}"
    if use_cache:
        cached = await redis.get(cache_key)
        if cached:
            return DashboardMetrics(**json.loads(cached))

    total_q = await db.execute(
        select(func.count()).select_from(Employee).where(Employee.status == EmployeeStatus.ACTIVE)
    )
    total = total_q.scalar() or 0
    summaries = await _summaries_today(db)

    present = sum(1 for s in summaries if s.check_in)
    absent = max(0, total - present)
    late = sum(1 for s in summaries if s.status == AttendanceStatus.LATE)
    overtime = sum(1 for s in summaries if s.overtime_minutes > 0)
    missing_checkout = sum(1 for s in summaries if s.workflow_status == WorkflowStatus.MISSING_CHECKOUT)

    breakdown = []
    dept_ids = {s.employee.department_id for s in summaries if s.employee.department_id}
    for dept_id in dept_ids:
        dept_summaries = [s for s in summaries if s.employee.department_id == dept_id]
        name = dept_summaries[0].employee.department.name if dept_summaries[0].employee.department else "Unknown"
        breakdown.append({
            "department": name,
            "present": sum(1 for s in dept_summaries if s.check_in),
            "total": len(dept_summaries),
        })

    metrics = DashboardMetrics(
        present_today=present,
        absent_today=absent,
        late_today=late,
        missing_checkout_today=missing_checkout,
        overtime_today=overtime,
        total_employees=total,
        active_employees=total,
        department_breakdown=breakdown,
    )
    await redis.setex(cache_key, 120, metrics.model_dump_json())
    return metrics


async def get_manager_metrics(db: AsyncSession, manager_employee_id) -> DashboardMetrics:
    team_result = await db.execute(
        select(Employee.id).where(Employee.manager_id == manager_employee_id)
    )
    team_ids = [r[0] for r in team_result.all()]
    if not team_ids:
        return DashboardMetrics(
            present_today=0, absent_today=0, late_today=0, missing_checkout_today=0,
            overtime_today=0, total_employees=0, active_employees=0, department_breakdown=[],
        )
    today = date.today()
    result = await db.execute(
        select(AttendanceSummary).where(
            AttendanceSummary.date == today,
            AttendanceSummary.employee_id.in_(team_ids),
        )
    )
    summaries = result.scalars().all()
    return DashboardMetrics(
        present_today=sum(1 for s in summaries if s.check_in),
        absent_today=len(team_ids) - sum(1 for s in summaries if s.check_in),
        late_today=sum(1 for s in summaries if s.status == AttendanceStatus.LATE),
        missing_checkout_today=sum(1 for s in summaries if s.workflow_status == WorkflowStatus.MISSING_CHECKOUT),
        overtime_today=sum(1 for s in summaries if s.overtime_minutes > 0),
        total_employees=len(team_ids),
        active_employees=len(team_ids),
        department_breakdown=[],
    )


async def get_employee_dashboard(db: AsyncSession, employee_id) -> EmployeeDashboard:
    from app.models.models import Employee
    from sqlalchemy.orm import selectinload

    today = date.today()
    summary_q = await db.execute(
        select(AttendanceSummary).where(
            AttendanceSummary.employee_id == employee_id,
            AttendanceSummary.date == today,
        )
    )
    today_summary = summary_q.scalar_one_or_none()
    month_start = today.replace(day=1)
    month_q = await db.execute(
        select(AttendanceSummary).where(
            AttendanceSummary.employee_id == employee_id,
            AttendanceSummary.date >= month_start,
        )
    )
    month_rows = month_q.scalars().all()
    emp_q = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.shift))
    )
    emp = emp_q.scalar_one_or_none()
    working_days = max(len(month_rows), 1)
    present_days = sum(1 for s in month_rows if s.check_in)
    pct = round(100.0 * present_days / working_days, 1)
    return EmployeeDashboard(
        today_status=today_summary.status.value if today_summary else None,
        workflow_status=today_summary.workflow_status.value if today_summary and today_summary.workflow_status else None,
        monthly_present=present_days,
        monthly_absent=sum(1 for s in month_rows if s.status == AttendanceStatus.ABSENT),
        check_in=today_summary.check_in if today_summary else None,
        check_out=today_summary.check_out if today_summary else None,
        worked_minutes=today_summary.worked_minutes if today_summary else 0,
        overtime_minutes=today_summary.overtime_minutes if today_summary else 0,
        shift_name=emp.shift.name if emp and emp.shift else None,
        attendance_percentage=pct,
    )


async def get_trends(db: AsyncSession, days: int = 30) -> DashboardTrends:
    from sqlalchemy import case, func

    redis = await get_redis()
    cache_key = f"dashboard:trends:{days}"
    cached = await redis.get(cache_key)
    if cached:
        return DashboardTrends(**json.loads(cached))

    end = date.today()
    start = end - timedelta(days=days - 1)
    q = await db.execute(
        select(
            AttendanceSummary.date,
            func.sum(case((AttendanceSummary.check_in.isnot(None), 1), else_=0)).label("present"),
            func.sum(case((AttendanceSummary.status == AttendanceStatus.ABSENT, 1), else_=0)).label("absent"),
            func.sum(case((AttendanceSummary.status == AttendanceStatus.LATE, 1), else_=0)).label("late"),
        )
        .where(AttendanceSummary.date >= start, AttendanceSummary.date <= end)
        .group_by(AttendanceSummary.date)
        .order_by(AttendanceSummary.date)
    )
    by_date = {row.date: row for row in q.all()}
    dates_list, present_list, absent_list, late_list = [], [], [], []
    current = start
    while current <= end:
        row = by_date.get(current)
        dates_list.append(current.isoformat())
        present_list.append(int(row.present) if row else 0)
        absent_list.append(int(row.absent) if row else 0)
        late_list.append(int(row.late) if row else 0)
        current += timedelta(days=1)

    trends = DashboardTrends(dates=dates_list, present=present_list, absent=absent_list, late=late_list)
    await redis.setex(cache_key, 300, trends.model_dump_json())
    return trends

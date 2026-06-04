from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AttendanceStatus,
    AttendanceSummary,
    User,
    UserRole,
    WorkflowStatus,
)
from app.services.notifications import notify_late_attendance, notify_missing_checkout


async def send_daily_hr_alerts(db: AsyncSession) -> int:
    """Email HR users about today's late arrivals and missing checkouts."""
    hr_result = await db.execute(
        select(User).where(
            User.role.in_((UserRole.SUPER_ADMIN, UserRole.HR_MANAGER)),
            User.is_active.is_(True),
            User.email_notifications.is_(True),
        )
    )
    hr_users = hr_result.scalars().all()
    if not hr_users:
        return 0

    today = date.today()
    summary_result = await db.execute(
        select(AttendanceSummary)
        .where(AttendanceSummary.date == today)
        .options(selectinload(AttendanceSummary.employee))
    )
    summaries = summary_result.scalars().all()
    sent = 0
    for summary in summaries:
        emp = summary.employee
        if summary.status == AttendanceStatus.LATE and summary.late_minutes > 0:
            for u in hr_users:
                if notify_late_attendance(u.email, emp.full_name, summary.late_minutes):
                    sent += 1
        if summary.workflow_status == WorkflowStatus.MISSING_CHECKOUT:
            for u in hr_users:
                if notify_missing_checkout(u.email, emp.full_name, today.isoformat()):
                    sent += 1
    return sent

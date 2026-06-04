from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import MANAGER_ROLES, require_roles
from app.models.models import AttendanceStatus, User
from app.schemas.schemas import ReportRow
from app.services import export as export_svc
from app.services import reports as report_svc
from app.services.audit import log_audit
from app.services.export_jobs import enqueue_export, get_job
from app.services.report_cache import cached_daily_report, cached_monthly_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _export_response(rows: list[ReportRow], fmt: str, filename: str) -> Response:
    fmt = (fmt or "csv").lower()
    if fmt == "csv":
        content = export_svc.to_csv(rows)
        media = "text/csv; charset=utf-8"
        if not filename.endswith(".csv"):
            filename = filename.rsplit(".", 1)[0] + ".csv"
    elif fmt in ("xlsx", "excel"):
        content = export_svc.to_excel(rows)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = filename.rsplit(".", 1)[0] + ".xlsx"
    elif fmt == "pdf":
        content = export_svc.to_pdf(rows, title=filename.rsplit(".", 1)[0].replace("_", " "))
        media = "application/pdf"
        filename = filename.rsplit(".", 1)[0] + ".pdf"
    else:
        content = export_svc.to_csv(rows)
        media = "text/csv; charset=utf-8"
        filename = filename.rsplit(".", 1)[0] + ".csv"
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _maybe_export(
    db: AsyncSession,
    user: User,
    rows: list[ReportRow],
    report_type: str,
    export_format: str | None,
    filename: str,
) -> list[ReportRow] | Response:
    if export_format:
        await log_audit(
            db,
            user.id,
            "report.exported",
            "reports",
            payload={"type": report_type, "format": export_format, "rows": len(rows)},
        )
        await db.commit()
        return _export_response(rows, export_format, filename)
    return rows


@router.get("/daily")
async def daily(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    report_date: date = Query(default_factory=date.today),
    department_id: UUID | None = None,
    export_format: str | None = Query(None, alias="format"),
):
    rows = await cached_daily_report(db, report_date, department_id)
    out = await _maybe_export(db, user, rows, "daily", export_format, f"daily_{report_date}.csv")
    return out if isinstance(out, Response) else [r.model_dump(mode="json", by_alias=True) for r in rows]


@router.get("/weekly")
async def weekly(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    week_start: date = Query(...),
    department_id: UUID | None = None,
    export_format: str | None = Query(None, alias="format"),
):
    rows = await report_svc.weekly_report(db, week_start, department_id)
    out = await _maybe_export(db, user, rows, "weekly", export_format, f"weekly_{week_start}.csv")
    return out if isinstance(out, Response) else [r.model_dump(mode="json", by_alias=True) for r in rows]


@router.get("/monthly")
async def monthly(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    department_id: UUID | None = None,
    export_format: str | None = Query(None, alias="format"),
):
    rows = await cached_monthly_report(db, year, month, department_id)
    out = await _maybe_export(db, user, rows, "monthly", export_format, f"monthly_{year}_{month:02d}.csv")
    return out if isinstance(out, Response) else [r.model_dump(mode="json", by_alias=True) for r in rows]


@router.get("/late")
async def late(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    start: date = Query(...),
    end: date = Query(...),
    department_id: UUID | None = None,
    export_format: str | None = Query(None, alias="format"),
):
    rows = await report_svc.filtered_report(db, start, end, AttendanceStatus.LATE, department_id)
    out = await _maybe_export(db, user, rows, "late", export_format, f"late_{start}_{end}.csv")
    return out if isinstance(out, Response) else [r.model_dump(mode="json", by_alias=True) for r in rows]


@router.get("/overtime")
async def overtime(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    start: date = Query(...),
    end: date = Query(...),
    department_id: UUID | None = None,
    export_format: str | None = Query(None, alias="format"),
):
    rows = await report_svc.filtered_report(db, start, end, AttendanceStatus.OVERTIME, department_id)
    out = await _maybe_export(db, user, rows, "overtime", export_format, f"overtime_{start}_{end}.csv")
    return out if isinstance(out, Response) else [r.model_dump(mode="json", by_alias=True) for r in rows]


@router.get("/absent")
async def absent(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    start: date = Query(...),
    end: date = Query(...),
    department_id: UUID | None = None,
    export_format: str | None = Query(None, alias="format"),
):
    rows = await report_svc.filtered_report(db, start, end, AttendanceStatus.ABSENT, department_id)
    out = await _maybe_export(db, user, rows, "absent", export_format, f"absent_{start}_{end}.csv")
    return out if isinstance(out, Response) else [r.model_dump(mode="json", by_alias=True) for r in rows]


@router.post("/jobs")
async def create_export_job(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
    report_type: str = Query(..., pattern="^(daily|monthly)$"),
    export_format: str = Query("csv", alias="format"),
    report_date: date | None = None,
    year: int | None = None,
    month: int | None = None,
    department_id: UUID | None = None,
):
    params: dict = {"department_id": str(department_id) if department_id else None}
    if report_type == "daily":
        params["date"] = (report_date or date.today()).isoformat()
    else:
        params["year"] = year or date.today().year
        params["month"] = month or date.today().month
    job_id = await enqueue_export(report_type, params, export_format, str(user.id))
    await log_audit(db, user.id, "report.job.queued", "reports", payload={"job_id": job_id, "type": report_type})
    await db.commit()
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}")
async def get_export_job(
    job_id: str,
    _: Annotated[User, Depends(require_roles(*MANAGER_ROLES))],
):
    job = await get_job(job_id)
    if not job:
        from fastapi import HTTPException

        raise HTTPException(404, "Job not found")
    return job

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.models import AuditLog, User, UserRole
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/api/admin/audit", tags=["audit"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN))],
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    pg = PaginationParams(page=page, page_size=page_size)
    total_q = await db.execute(select(func.count()).select_from(AuditLog))
    total = total_q.scalar() or 0
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(pg.offset)
        .limit(pg.page_size)
    )
    items = list(result.scalars().all())
    pages = max(1, (total + pg.page_size - 1) // pg.page_size)
    return PaginatedResponse(
        items=items,
        total=total,
        page=pg.page,
        page_size=pg.page_size,
        pages=pages,
    )

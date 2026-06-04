from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuditLog


async def log_audit(
    db: AsyncSession,
    actor_id: UUID | None,
    action: str,
    resource: str,
    ip_address: str | None = None,
    payload: dict | None = None,
) -> None:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        payload_json=payload,
    )
    db.add(entry)

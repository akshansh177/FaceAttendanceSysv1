from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from app.core.redis_client import get_redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AttendanceKiosk,
    AttendanceMode,
    AttendancePolicy,
    Employee,
    PolicyScopeType,
)


SCOPE_ORDER = [
    PolicyScopeType.EMPLOYEE,
    PolicyScopeType.JOB_ROLE,
    PolicyScopeType.DEPARTMENT,
    PolicyScopeType.LOCATION,
    PolicyScopeType.SHIFT,
]


POLICY_CACHE_KEY = "cache:policies:active"


async def warm_policy_cache(db: AsyncSession) -> int:
    result = await db.execute(
        select(AttendancePolicy).where(AttendancePolicy.is_active.is_(True))
    )
    policies = list(result.scalars().all())
    payload = [
        {
            "scope_type": p.scope_type.value,
            "scope_id": str(p.scope_id) if p.scope_id else None,
            "priority": p.priority,
            "rules_json": p.rules_json or {},
        }
        for p in policies
    ]
    redis = await get_redis()
    await redis.setex(POLICY_CACHE_KEY, 900, json.dumps(payload))
    return len(payload)


async def invalidate_policy_cache() -> None:
    redis = await get_redis()
    await redis.delete(POLICY_CACHE_KEY)


async def get_effective_rules(db: AsyncSession, employee: Employee) -> dict:
    redis = await get_redis()
    cached = await redis.get(POLICY_CACHE_KEY)
    if cached:
        policy_rows = json.loads(cached)
    else:
        result = await db.execute(
            select(AttendancePolicy).where(AttendancePolicy.is_active.is_(True))
        )
        policy_rows = [
            {
                "scope_type": p.scope_type.value,
                "scope_id": str(p.scope_id) if p.scope_id else None,
                "priority": p.priority,
                "rules_json": p.rules_json or {},
            }
            for p in result.scalars().all()
        ]
    policies = policy_rows
    merged: dict = {}

    def scope_id_for(pt: PolicyScopeType) -> UUID | None:
        if pt == PolicyScopeType.EMPLOYEE:
            return employee.id
        if pt == PolicyScopeType.JOB_ROLE:
            return employee.job_role_id
        if pt == PolicyScopeType.DEPARTMENT:
            return employee.department_id
        if pt == PolicyScopeType.SHIFT:
            return employee.shift_id
        return None

    location_ids = [loc.id for loc in employee.locations] if employee.locations else []

    for scope_type in SCOPE_ORDER:
        st_val = scope_type.value
        candidates = [p for p in policies if p["scope_type"] == st_val]
        candidates.sort(key=lambda p: p["priority"])
        for policy in candidates:
            pid = policy["scope_id"]
            if scope_type == PolicyScopeType.LOCATION:
                if pid and pid not in {str(lid) for lid in location_ids}:
                    continue
            else:
                sid = scope_id_for(scope_type)
                if pid and sid and pid != str(sid):
                    continue
                if pid and not sid:
                    continue
            merged.update(policy["rules_json"] or {})

    return merged


async def validate_kiosk_policy(
    db: AsyncSession,
    employee: Employee,
    kiosk: AttendanceKiosk,
) -> tuple[bool, str | None]:
    result = await db.execute(
        select(Employee)
        .where(Employee.id == employee.id)
        .options(selectinload(Employee.locations), selectinload(Employee.allowed_kiosks))
    )
    emp = result.scalar_one()

    access = await db.execute(
        select(AttendanceKiosk)
        .where(AttendanceKiosk.id == kiosk.id)
        .options(selectinload(AttendanceKiosk.allowed_employees))
    )
    kiosk_loaded = access.scalar_one()
    if kiosk_loaded.allowed_employees and emp.id not in {e.id for e in kiosk_loaded.allowed_employees}:
        return False, "You are not allowed to use this kiosk"

    rules = await get_effective_rules(db, emp)
    allowed_ids = rules.get("allowed_kiosk_ids")
    if allowed_ids and str(kiosk.id) not in {str(x) for x in allowed_ids}:
        return False, "Kiosk not authorized for your profile"

    if kiosk.department_id and emp.department_id and kiosk.department_id != emp.department_id:
        dept_only = rules.get("kiosk_department_only", False)
        if dept_only:
            return False, "This kiosk is restricted to another department"

    return True, None


def attendance_mode_override(rules: dict) -> AttendanceMode | None:
    raw = rules.get("attendance_mode_override")
    if not raw:
        return None
    try:
        return AttendanceMode(raw)
    except ValueError:
        return None

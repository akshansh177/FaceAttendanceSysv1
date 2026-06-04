from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import HR_ROLES, require_roles
from app.models.models import Employee, Location, User, employee_locations
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.schemas import (
    EmployeeCreate,
    EmployeeLocationsUpdate,
    EmployeeResponse,
    EmployeeUpdate,
    MessageResponse,
)
from app.services.audit import log_audit

router = APIRouter(prefix="/api/employees", tags=["employees"])


def _to_response(emp: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=emp.id,
        employee_code=emp.employee_code,
        full_name=emp.full_name,
        email=emp.email,
        phone=emp.phone,
        department_id=emp.department_id,
        job_role_id=emp.job_role_id,
        shift_id=emp.shift_id,
        manager_id=emp.manager_id,
        employment_type=emp.employment_type,
        joining_date=emp.joining_date,
        status=emp.status,
        profile_photo_path=emp.profile_photo_path,
        location_ids=[loc.id for loc in emp.locations] if emp.locations else [],
        created_at=emp.created_at,
    )


async def _assign_locations(db: AsyncSession, emp: Employee, location_ids: list[UUID]) -> None:
    """Assign M2M locations without triggering async-incompatible lazy loads."""
    await db.execute(
        delete(employee_locations).where(employee_locations.c.employee_id == emp.id)
    )
    locations: list[Location] = []
    if location_ids:
        result = await db.execute(select(Location).where(Location.id.in_(location_ids)))
        locations = list(result.scalars().all())
        if len(locations) != len(set(location_ids)):
            raise HTTPException(400, "One or more location IDs are invalid")
        await db.execute(
            insert(employee_locations),
            [{"employee_id": emp.id, "location_id": loc.id} for loc in locations],
        )
    set_committed_value(emp, "locations", locations)


async def _reload_employee(db: AsyncSession, employee_id: UUID) -> Employee:
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.locations))
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    return emp


@router.get("", response_model=PaginatedResponse[EmployeeResponse])
async def list_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    pg = PaginationParams(page=page, page_size=page_size)
    total_q = await db.execute(select(func.count()).select_from(Employee))
    total = total_q.scalar() or 0
    result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.locations))
        .order_by(Employee.full_name)
        .offset(pg.offset)
        .limit(pg.page_size)
    )
    items = [_to_response(e) for e in result.scalars().all()]
    pages = max(1, (total + pg.page_size - 1) // pg.page_size)
    return PaginatedResponse(
        items=items,
        total=total,
        page=pg.page,
        page_size=pg.page_size,
        pages=pages,
    )


@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    body: EmployeeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    existing = await db.execute(select(Employee).where(Employee.employee_code == body.employee_code))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Employee code '{body.employee_code}' already exists")

    data = body.model_dump(exclude={"location_ids"})
    emp = Employee(**data)
    db.add(emp)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        if "email" in str(e.orig).lower():
            raise HTTPException(409, "Email already in use") from e
        raise HTTPException(409, "Employee already exists") from e
    await _assign_locations(db, emp, body.location_ids)
    await log_audit(db, user.id, "employee.created", "employees", payload={"code": body.employee_code})
    emp = await _reload_employee(db, emp.id)
    return _to_response(emp)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.locations))
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    return _to_response(emp)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    body: EmployeeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.locations))
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(emp, k, v)
    await log_audit(db, user.id, "employee.updated", "employees", payload={"id": str(employee_id)})
    await db.refresh(emp, ["locations"])
    return _to_response(emp)


@router.post("/{employee_id}/locations", response_model=EmployeeResponse)
async def set_employee_locations(
    employee_id: UUID,
    body: EmployeeLocationsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.locations))
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    await _assign_locations(db, emp, body.location_ids)
    emp = await _reload_employee(db, employee_id)
    return _to_response(emp)


@router.delete("/{employee_id}", response_model=MessageResponse)
async def delete_employee(
    employee_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(*HR_ROLES))],
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    await db.delete(emp)
    await log_audit(db, user.id, "employee.deleted", "employees", payload={"id": str(employee_id)})
    return MessageResponse(message="Employee deleted")


@router.post("/{employee_id}/photo", response_model=EmployeeResponse)
async def upload_photo(
    employee_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(*HR_ROLES)),
):
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id).options(selectinload(Employee.locations))
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / "photos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
    path = upload_dir / f"{employee_id}{ext}"
    with path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    emp.profile_photo_path = str(path)
    await log_audit(db, user.id, "employee.photo.updated", "employees")
    await db.refresh(emp, ["locations"])
    return _to_response(emp)

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
    Time,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def str_enum(enum_cls: type[enum.Enum], **kwargs: object) -> Enum:
    return Enum(
        enum_cls,
        values_callable=lambda x: [e.value for e in x],
        native_enum=False,
        length=50,
        **kwargs,
    )


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    HR_MANAGER = "hr_manager"
    TEAM_MANAGER = "team_manager"
    EMPLOYEE = "employee"


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class ShiftType(str, enum.Enum):
    FIXED = "fixed"
    ROTATIONAL = "rotational"
    NIGHT = "night"
    FLEXIBLE = "flexible"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EARLY_LEAVE = "early_leave"
    HALF_DAY = "half_day"
    OVERTIME = "overtime"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"
    ON_LEAVE = "on_leave"


class WorkflowStatus(str, enum.Enum):
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    MISSING_CHECKOUT = "missing_checkout"


class AttendanceMode(str, enum.Enum):
    FACE_ONLY = "face_only"
    FACE_GPS = "face_gps"
    FACE_NETWORK = "face_network"
    FACE_GPS_DEVICE = "face_gps_device"


class AttendanceMethod(str, enum.Enum):
    KIOSK_ONLY = "kiosk_only"
    PORTAL_ONLY = "portal_only"
    KIOSK_PORTAL = "kiosk_portal"
    MOBILE_APP = "mobile_app"
    ANY = "any"


class KioskStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"


class PolicyScopeType(str, enum.Enum):
    EMPLOYEE = "employee"
    DEPARTMENT = "department"
    JOB_ROLE = "job_role"
    LOCATION = "location"
    SHIFT = "shift"


class DeviceType(str, enum.Enum):
    KIOSK = "kiosk"
    MOBILE = "mobile"
    TABLET = "tablet"


class DeviceStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REVOKED = "revoked"


class CorrectionStatus(str, enum.Enum):
    PENDING_MANAGER = "pending_manager"
    PENDING_HR = "pending_hr"
    APPROVED = "approved"
    REJECTED = "rejected"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class HolidayScope(str, enum.Enum):
    GLOBAL = "global"
    DEPARTMENT = "department"


employee_locations = Table(
    "employee_locations",
    Base.metadata,
    Column("employee_id", Uuid(as_uuid=True), ForeignKey("employees.id"), primary_key=True),
    Column("location_id", Uuid(as_uuid=True), ForeignKey("locations.id"), primary_key=True),
)

kiosk_employee_access = Table(
    "kiosk_employee_access",
    Base.metadata,
    Column("kiosk_id", Uuid(as_uuid=True), ForeignKey("attendance_kiosks.id"), primary_key=True),
    Column("employee_id", Uuid(as_uuid=True), ForeignKey("employees.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(str_enum(UserRole), default=UserRole.EMPLOYEE)
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[Optional["Employee"]] = relationship(back_populates="user")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class JobRole(Base):
    __tablename__ = "job_roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permission_flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employees: Mapped[list["Employee"]] = relationship(back_populates="job_role")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius_meters: Mapped[int] = mapped_column(Integer, default=200)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employees: Mapped[list["Employee"]] = relationship(
        secondary=employee_locations, back_populates="locations"
    )
    devices: Mapped[list["Device"]] = relationship(back_populates="location")
    kiosks: Mapped[list["AttendanceKiosk"]] = relationship(back_populates="location")


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    grace_minutes: Mapped[int] = mapped_column(Integer, default=15)
    shift_type: Mapped[ShiftType] = mapped_column(str_enum(ShiftType), default=ShiftType.FIXED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employees: Mapped[list["Employee"]] = relationship(back_populates="shift")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    job_role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("job_roles.id"), nullable=True
    )
    shift_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("shifts.id"), nullable=True
    )
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        str_enum(EmploymentType), default=EmploymentType.FULL_TIME
    )
    joining_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[EmployeeStatus] = mapped_column(str_enum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    profile_photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department: Mapped[Optional["Department"]] = relationship(back_populates="employees")
    job_role: Mapped[Optional["JobRole"]] = relationship(back_populates="employees")
    shift: Mapped[Optional["Shift"]] = relationship(back_populates="employees")
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", remote_side="Employee.id", foreign_keys=[manager_id]
    )
    user: Mapped[Optional["User"]] = relationship(back_populates="employee")
    locations: Mapped[list["Location"]] = relationship(
        secondary=employee_locations, back_populates="employees"
    )
    face_embeddings: Mapped[list["FaceEmbedding"]] = relationship(back_populates="employee")
    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(back_populates="employee")
    summaries: Mapped[list["AttendanceSummary"]] = relationship(back_populates="employee")
    corrections: Mapped[list["AttendanceCorrection"]] = relationship(back_populates="employee")
    allowed_kiosks: Mapped[list["AttendanceKiosk"]] = relationship(
        secondary=kiosk_employee_access, back_populates="allowed_employees"
    )


class OrganizationSettings(Base):
    __tablename__ = "organization_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_mode: Mapped[AttendanceMode] = mapped_column(
        str_enum(AttendanceMode), default=AttendanceMode.FACE_ONLY
    )
    attendance_method: Mapped[AttendanceMethod] = mapped_column(
        str_enum(AttendanceMethod), default=AttendanceMethod.KIOSK_PORTAL
    )
    gps_enforcement_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    device_enforcement_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_ip_cidrs: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    kiosk_checkout_after_checkout: Mapped[str] = mapped_column(String(20), default="ignore")
    kiosk_screen_reset_seconds: Mapped[int] = mapped_column(Integer, default=5)
    voice_feedback_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    voice_language: Mapped[str] = mapped_column(String(10), default="en")
    match_threshold_preset: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    match_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AttendanceKiosk(Base):
    __tablename__ = "attendance_kiosks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    device_identifier: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    status: Mapped[KioskStatus] = mapped_column(str_enum(KioskStatus), default=KioskStatus.ACTIVE)
    api_key_hash: Mapped[str] = mapped_column(String(255))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped[Optional["Location"]] = relationship(back_populates="kiosks")
    department: Mapped[Optional["Department"]] = relationship()
    allowed_employees: Mapped[list["Employee"]] = relationship(
        secondary=kiosk_employee_access, back_populates="allowed_kiosks"
    )
    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(back_populates="kiosk")


class AttendancePolicy(Base):
    __tablename__ = "attendance_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    scope_type: Mapped[PolicyScopeType] = mapped_column(str_enum(PolicyScopeType))
    scope_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    rules_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    embedding_vector: Mapped[bytes] = mapped_column(LargeBinary)
    model: Mapped[str] = mapped_column(String(50), default="insightface")
    encrypted: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="face_embeddings")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    device_type: Mapped[DeviceType] = mapped_column(str_enum(DeviceType), default=DeviceType.KIOSK)
    mac_address: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    legacy_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(str_enum(DeviceStatus), default=DeviceStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped[Optional["Location"]] = relationship(back_populates="devices")


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    kiosk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("attendance_kiosks.id"), nullable=True, index=True
    )
    recognition_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    event_type: Mapped[str] = mapped_column(String(20), default="recognize")
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    employee: Mapped["Employee"] = relationship(back_populates="attendance_logs")
    kiosk: Mapped[Optional["AttendanceKiosk"]] = relationship(back_populates="attendance_logs")


class AttendanceSummary(Base):
    __tablename__ = "attendance_summary"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    check_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        str_enum(AttendanceStatus), default=AttendanceStatus.ABSENT
    )
    workflow_status: Mapped[Optional[WorkflowStatus]] = mapped_column(str_enum(WorkflowStatus), nullable=True)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    worked_minutes: Mapped[int] = mapped_column(Integer, default=0)
    expected_minutes: Mapped[int] = mapped_column(Integer, default=0)

    employee: Mapped["Employee"] = relationship(back_populates="summaries")


class AttendanceCorrection(Base):
    __tablename__ = "attendance_corrections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    requested_check_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_check_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[CorrectionStatus] = mapped_column(
        str_enum(CorrectionStatus), default=CorrectionStatus.PENDING_MANAGER
    )
    manager_approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    hr_approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    manager_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    hr_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="corrections")


class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    date: Mapped[date] = mapped_column(Date, index=True)
    scope: Mapped[HolidayScope] = mapped_column(str_enum(HolidayScope), default=HolidayScope.GLOBAL)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[LeaveStatus] = mapped_column(str_enum(LeaveStatus), default=LeaveStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource: Mapped[str] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

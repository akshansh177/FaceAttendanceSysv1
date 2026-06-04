from __future__ import annotations

from datetime import date, datetime, time
from datetime import date as DateType
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.models import (
    AttendanceMethod,
    AttendanceMode,
    AttendanceStatus,
    CorrectionStatus,
    DeviceStatus,
    DeviceType,
    EmployeeStatus,
    EmploymentType,
    HolidayScope,
    KioskStatus,
    LeaveStatus,
    PolicyScopeType,
    ShiftType,
    UserRole,
    WorkflowStatus,
)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    employee_code: str | None = None
    password: str

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.email and not self.employee_code:
            raise ValueError("email or employee_code required")
        return self


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: UserRole
    employee_id: UUID | None
    is_active: bool

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobRoleCreate(BaseModel):
    name: str
    description: str | None = None
    permission_flags: dict | None = None


class JobRoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    permission_flags: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LocationCreate(BaseModel):
    name: str
    address: str | None = None
    latitude: float
    longitude: float
    radius_meters: int = 200
    is_active: bool = True


class LocationResponse(BaseModel):
    id: UUID
    name: str
    address: str | None
    latitude: float
    longitude: float
    radius_meters: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeLocationsUpdate(BaseModel):
    location_ids: list[UUID]


class ShiftCreate(BaseModel):
    name: str
    start_time: time
    end_time: time
    grace_minutes: int = 15
    shift_type: ShiftType = ShiftType.FIXED


class ShiftUpdate(BaseModel):
    name: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    grace_minutes: int | None = None
    shift_type: ShiftType | None = None


class ShiftResponse(BaseModel):
    id: UUID
    name: str
    start_time: time
    end_time: time
    grace_minutes: int
    shift_type: ShiftType
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeCreate(BaseModel):
    employee_code: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    department_id: UUID | None = None
    job_role_id: UUID | None = None
    shift_id: UUID | None = None
    manager_id: UUID | None = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    joining_date: date | None = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    location_ids: list[UUID] = []


class EmployeeUpdate(BaseModel):
    employee_code: str | None = None
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    department_id: UUID | None = None
    job_role_id: UUID | None = None
    shift_id: UUID | None = None
    manager_id: UUID | None = None
    employment_type: EmploymentType | None = None
    joining_date: date | None = None
    status: EmployeeStatus | None = None


class EmployeeResponse(BaseModel):
    id: UUID
    employee_code: str
    full_name: str
    email: str
    phone: str | None
    department_id: UUID | None
    job_role_id: UUID | None
    shift_id: UUID | None
    manager_id: UUID | None
    employment_type: EmploymentType
    joining_date: date | None
    status: EmployeeStatus
    profile_photo_path: str | None
    location_ids: list[UUID] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class FaceEnrollResponse(BaseModel):
    employee_id: UUID
    embeddings_stored: int
    message: str


class FaceStatusResponse(BaseModel):
    employee_id: UUID
    embedding_count: int
    models: list[str]


class RecognizeResponse(BaseModel):
    matched: bool
    employee_id: UUID | None = None
    employee_name: str | None = None
    score: float | None = None
    event: str | None = None
    message: str
    duplicate: bool = False


class AttendanceSummaryResponse(BaseModel):
    id: UUID
    employee_id: UUID
    date: date
    check_in: datetime | None
    check_out: datetime | None
    status: AttendanceStatus
    workflow_status: WorkflowStatus | None = None
    late_minutes: int
    overtime_minutes: int
    worked_minutes: int = 0
    expected_minutes: int = 0

    model_config = {"from_attributes": True}


class AttendanceSettingsUpdate(BaseModel):
    attendance_mode: AttendanceMode | None = None
    attendance_method: AttendanceMethod | None = None
    gps_enforcement_enabled: bool | None = None
    device_enforcement_enabled: bool | None = None
    allowed_ip_cidrs: list[str] | None = None
    kiosk_checkout_after_checkout: str | None = None
    kiosk_screen_reset_seconds: int | None = None
    voice_feedback_enabled: bool | None = None
    voice_language: str | None = None
    match_threshold_preset: str | None = None
    match_threshold: float | None = None


class AttendanceSettingsResponse(BaseModel):
    attendance_mode: AttendanceMode
    attendance_method: AttendanceMethod
    gps_enforcement_enabled: bool
    device_enforcement_enabled: bool
    allowed_ip_cidrs: list[str] | None
    kiosk_checkout_after_checkout: str
    kiosk_screen_reset_seconds: int
    voice_feedback_enabled: bool
    voice_language: str
    match_threshold_preset: str | None = None
    match_threshold: float | None = None
    effective_match_threshold: float = 0.70

    model_config = {"from_attributes": True}


class DeviceCreate(BaseModel):
    device_id: str
    name: str
    device_type: DeviceType = DeviceType.KIOSK
    mac_address: str | None = None
    location_id: UUID | None = None
    status: DeviceStatus = DeviceStatus.PENDING


class DeviceUpdate(BaseModel):
    name: str | None = None
    device_type: DeviceType | None = None
    mac_address: str | None = None
    location_id: UUID | None = None
    status: DeviceStatus | None = None


class DeviceResponse(BaseModel):
    id: UUID
    device_id: str
    name: str
    device_type: DeviceType
    mac_address: str | None
    location_id: UUID | None
    status: DeviceStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class CorrectionCreate(BaseModel):
    date: date
    requested_check_in: datetime | None = None
    requested_check_out: datetime | None = None
    reason: str


class CorrectionResponse(BaseModel):
    id: UUID
    employee_id: UUID
    date: date
    requested_check_in: datetime | None
    requested_check_out: datetime | None
    reason: str
    status: CorrectionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class HolidayCreate(BaseModel):
    name: str
    date: date
    scope: HolidayScope = HolidayScope.GLOBAL
    department_id: UUID | None = None


class HolidayResponse(BaseModel):
    id: UUID
    name: str
    date: date
    scope: HolidayScope
    department_id: UUID | None

    model_config = {"from_attributes": True}


class LeaveCreate(BaseModel):
    employee_id: UUID
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveUpdate(BaseModel):
    status: LeaveStatus


class LeaveResponse(BaseModel):
    id: UUID
    employee_id: UUID
    start_date: date
    end_date: date
    reason: str | None
    status: LeaveStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardMetrics(BaseModel):
    present_today: int
    absent_today: int
    late_today: int
    missing_checkout_today: int = 0
    overtime_today: int
    total_employees: int
    active_employees: int
    department_breakdown: list[dict]


class EmployeeDashboard(BaseModel):
    today_status: str | None
    workflow_status: str | None
    monthly_present: int
    monthly_absent: int
    leave_balance_placeholder: int = 0
    check_in: datetime | None = None
    check_out: datetime | None = None
    worked_minutes: int = 0
    overtime_minutes: int = 0
    shift_name: str | None = None
    attendance_percentage: float = 0.0


class DashboardTrends(BaseModel):
    dates: list[str]
    present: list[int]
    absent: list[int]
    late: list[int]


class ReportRow(BaseModel):
    """Use attendance_date field name — a field named `date` breaks Pydantic type resolution."""

    model_config = ConfigDict(populate_by_name=True)

    employee_code: str
    full_name: str
    department: str | None = None
    attendance_date: DateType | None = Field(default=None, alias="date")
    check_in: str | None = None
    check_out: str | None = None
    status: str
    late_minutes: int = 0
    overtime_minutes: int = 0


class AuditLogResponse(BaseModel):
    id: UUID
    actor_id: UUID | None
    action: str
    resource: str
    ip_address: str | None
    payload_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str


class KioskRecognizeResponse(BaseModel):
    matched: bool
    status: str
    code: str
    display_message: str
    employee_id: UUID | None = None
    photo_url: str | None = None
    full_name: str | None = None
    employee_code: str | None = None
    department: str | None = None
    job_role: str | None = None
    current_time: datetime | None = None
    attendance_status: str | None = None
    event: str | None = None
    score: float | None = None


class KioskConfigResponse(BaseModel):
    screen_reset_seconds: int
    voice_feedback_enabled: bool
    voice_language: str
    company_name: str = "Face Attendance"


class KioskCreate(BaseModel):
    name: str
    device_identifier: str
    location_id: UUID | None = None
    department_id: UUID | None = None
    status: KioskStatus = KioskStatus.ACTIVE
    employee_ids: list[UUID] = []


class KioskUpdate(BaseModel):
    name: str | None = None
    location_id: UUID | None = None
    department_id: UUID | None = None
    status: KioskStatus | None = None
    employee_ids: list[UUID] | None = None


class KioskResponse(BaseModel):
    id: UUID
    name: str
    device_identifier: str
    location_id: UUID | None
    department_id: UUID | None
    status: KioskStatus
    last_seen: datetime | None
    is_online: bool = False
    created_at: datetime
    employee_ids: list[UUID] = []

    model_config = {"from_attributes": True}


class KioskCreateResponse(KioskResponse):
    api_key: str


class PolicyCreate(BaseModel):
    name: str
    scope_type: PolicyScopeType
    scope_id: UUID | None = None
    priority: int = 100
    rules_json: dict = {}
    is_active: bool = True


class PolicyResponse(BaseModel):
    id: UUID
    name: str
    scope_type: PolicyScopeType
    scope_id: UUID | None
    priority: int
    rules_json: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LiveFeedItem(BaseModel):
    id: str
    employee_name: str
    employee_code: str | None = None
    department: str | None = None
    job_role: str | None = None
    event_type: str
    timestamp: str
    kiosk_name: str | None = None
    location: str | None = None


class EmployeeProfileResponse(BaseModel):
    id: UUID
    employee_code: str
    full_name: str
    email: str
    phone: str | None
    department: str | None
    job_role: str | None
    shift_name: str | None
    profile_photo_path: str | None

    model_config = {"from_attributes": True}


class EmployeeProfileUpdate(BaseModel):
    phone: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class CalendarDay(BaseModel):
    date: date
    status: str
    check_in: datetime | None = None
    check_out: datetime | None = None


class ShiftInfoResponse(BaseModel):
    name: str
    start_time: time
    end_time: time
    grace_minutes: int
    shift_type: ShiftType

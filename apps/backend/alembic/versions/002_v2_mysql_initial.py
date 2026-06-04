"""v2 mysql initial schema

Revision ID: 002
Revises:
Create Date: 2026-06-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "job_roles",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("permission_flags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "locations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_meters", sa.Integer(), default=200),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "shifts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("grace_minutes", sa.Integer(), default=15),
        sa.Column("shift_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "employees",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("employee_code", sa.String(50), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("job_role_id", UUID, sa.ForeignKey("job_roles.id"), nullable=True),
        sa.Column("shift_id", UUID, sa.ForeignKey("shifts.id"), nullable=True),
        sa.Column("manager_id", UUID, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=False),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("profile_photo_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_employees_code", "employees", ["employee_code"])
    op.create_table(
        "employee_locations",
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), primary_key=True),
        sa.Column("location_id", UUID, sa.ForeignKey("locations.id"), primary_key=True),
    )
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("email_notifications", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "organization_settings",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("attendance_mode", sa.String(50), nullable=False),
        sa.Column("gps_enforcement_enabled", sa.Boolean(), default=False),
        sa.Column("device_enforcement_enabled", sa.Boolean(), default=False),
        sa.Column("allowed_ip_cidrs", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "face_embeddings",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("embedding_vector", sa.LargeBinary(), nullable=False),
        sa.Column("model", sa.String(50)),
        sa.Column("encrypted", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "devices",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("device_id", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("mac_address", sa.String(50), unique=True, nullable=True),
        sa.Column("location_id", UUID, sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("legacy_location", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "attendance_logs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("recognition_score", sa.Float(), nullable=True),
        sa.Column("event_type", sa.String(20)),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
    )
    op.create_index("ix_attendance_logs_employee_ts", "attendance_logs", ["employee_id", "timestamp"])
    op.create_table(
        "attendance_summary",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("workflow_status", sa.String(50), nullable=True),
        sa.Column("late_minutes", sa.Integer(), default=0),
        sa.Column("overtime_minutes", sa.Integer(), default=0),
        sa.Column("worked_minutes", sa.Integer(), default=0),
        sa.Column("expected_minutes", sa.Integer(), default=0),
    )
    op.create_index("ix_attendance_summary_emp_date", "attendance_summary", ["employee_id", "date"])
    op.create_table(
        "attendance_corrections",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("requested_check_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("manager_approved_by", UUID, nullable=True),
        sa.Column("hr_approved_by", UUID, nullable=True),
        sa.Column("manager_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hr_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_corrections_status", "attendance_corrections", ["status"])
    op.create_table(
        "holidays",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
    )
    op.create_table(
        "leave_requests",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("actor_id", UUID, nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_created", "audit_logs", ["created_at"])


def downgrade() -> None:
    for t in [
        "audit_logs", "leave_requests", "holidays", "attendance_corrections",
        "attendance_summary", "attendance_logs", "devices", "face_embeddings",
        "organization_settings", "users", "employee_locations", "employees",
        "shifts", "locations", "job_roles", "departments",
    ]:
        op.drop_table(t)

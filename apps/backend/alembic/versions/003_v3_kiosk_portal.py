"""v3 kiosk portal schema

Revision ID: 003
Revises: 002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "attendance_kiosks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("device_identifier", sa.String(100), unique=True, nullable=False),
        sa.Column("location_id", UUID, sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("api_key_hash", sa.String(255), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "kiosk_employee_access",
        sa.Column("kiosk_id", UUID, sa.ForeignKey("attendance_kiosks.id"), primary_key=True),
        sa.Column("employee_id", UUID, sa.ForeignKey("employees.id"), primary_key=True),
    )
    op.create_table(
        "attendance_policies",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scope_type", sa.String(50), nullable=False),
        sa.Column("scope_id", UUID, nullable=True),
        sa.Column("priority", sa.Integer(), default=100),
        sa.Column("rules_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column(
        "organization_settings",
        sa.Column("attendance_method", sa.String(50), server_default="kiosk_portal"),
    )
    op.add_column(
        "organization_settings",
        sa.Column("kiosk_checkout_after_checkout", sa.String(20), server_default="ignore"),
    )
    op.add_column(
        "organization_settings",
        sa.Column("kiosk_screen_reset_seconds", sa.Integer(), server_default="5"),
    )
    op.add_column(
        "organization_settings",
        sa.Column("voice_feedback_enabled", sa.Boolean(), server_default="1"),
    )
    op.add_column(
        "organization_settings",
        sa.Column("voice_language", sa.String(10), server_default="en"),
    )
    op.add_column(
        "attendance_logs",
        sa.Column("kiosk_id", UUID, sa.ForeignKey("attendance_kiosks.id"), nullable=True),
    )
    op.create_index("ix_attendance_logs_kiosk_ts", "attendance_logs", ["kiosk_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_attendance_logs_kiosk_ts", "attendance_logs")
    op.drop_column("attendance_logs", "kiosk_id")
    for col in [
        "voice_language",
        "voice_feedback_enabled",
        "kiosk_screen_reset_seconds",
        "kiosk_checkout_after_checkout",
        "attendance_method",
    ]:
        op.drop_column("organization_settings", col)
    op.drop_table("attendance_policies")
    op.drop_table("kiosk_employee_access")
    op.drop_table("attendance_kiosks")

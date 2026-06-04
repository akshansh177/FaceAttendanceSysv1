"""Performance indexes and unique attendance summary constraint

Revision ID: 004
Revises: 003
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_attendance_summary_date", "attendance_summary", ["date"], unique=False)
    op.create_index(
        "ix_attendance_summary_status_date",
        "attendance_summary",
        ["status", "date"],
        unique=False,
    )
    op.create_index("ix_employees_department_id", "employees", ["department_id"], unique=False)
    try:
        op.create_unique_constraint(
            "uq_attendance_summary_employee_date",
            "attendance_summary",
            ["employee_id", "date"],
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint("uq_attendance_summary_employee_date", "attendance_summary", type_="unique")
    except Exception:
        pass
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_index("ix_attendance_summary_status_date", table_name="attendance_summary")
    op.drop_index("ix_attendance_summary_date", table_name="attendance_summary")

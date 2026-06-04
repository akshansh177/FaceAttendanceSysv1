"""Add match threshold preset columns to organization_settings."""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organization_settings",
        sa.Column("match_threshold_preset", sa.String(32), nullable=True),
    )
    op.add_column(
        "organization_settings",
        sa.Column("match_threshold", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organization_settings", "match_threshold")
    op.drop_column("organization_settings", "match_threshold_preset")

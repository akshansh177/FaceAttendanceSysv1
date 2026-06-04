"""legacy placeholder (PostgreSQL schema moved to 002 for MySQL)

Revision ID: 001
Revises:
Create Date: 2026-06-04

V1 PostgreSQL DDL was removed. Fresh V2 installs apply 002 only.
"""
from typing import Sequence, Union

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

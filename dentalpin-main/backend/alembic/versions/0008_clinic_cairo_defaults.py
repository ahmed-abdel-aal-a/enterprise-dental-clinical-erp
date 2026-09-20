"""core — set clinics default timezone to Africa/Cairo and currency to EGP, and normalize existing rows.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-19
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update column defaults for clinics table
    op.alter_column(
        "clinics",
        "timezone",
        existing_type=sa.String(length=64),
        server_default="Africa/Cairo",
    )
    op.alter_column(
        "clinics",
        "currency",
        existing_type=sa.String(length=3),
        server_default="EGP",
    )

    # 2. Normalize existing clinics records
    op.execute(
        """
        UPDATE clinics
        SET timezone = 'Africa/Cairo', currency = 'EGP'
        WHERE timezone IS NULL OR timezone = 'Europe/Madrid';
        """
    )


def downgrade() -> None:
    op.alter_column(
        "clinics",
        "timezone",
        existing_type=sa.String(length=64),
        server_default="Europe/Madrid",
    )
    op.alter_column(
        "clinics",
        "currency",
        existing_type=sa.String(length=3),
        server_default="EUR",
    )

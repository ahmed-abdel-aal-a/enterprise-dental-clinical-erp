"""Reinterpret stored appointment times as clinic-local (issue #161).

Before this fix the frontend sent naive clinic-local wall-clock times and
the backend persisted them unconverted into ``timestamptz`` columns, so
"11:00 America/Lima" was stored as "11:00 UTC". This migration shifts
``start_time``/``end_time`` so the stored instant matches the wall-clock
the user originally entered, per each clinic's configured timezone.
``AT TIME ZONE`` handles DST per row.

Caveat: rows created through the API with an explicit UTC offset (no known
client did this — the bundled frontend always sent naive values) would be
shifted incorrectly. There is no way to tell them apart.

Audit columns (``created_at``, ``current_status_since``, ...) were always
server-generated real UTC and are left untouched.

Revision ID: ag_0006
Revises: ag_0005
Create Date: 2026-08-09

"""

from collections.abc import Sequence

from alembic import op

revision: str = "ag_0006"
down_revision: str | None = "ag_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE appointments a
        SET start_time = (a.start_time AT TIME ZONE 'UTC') AT TIME ZONE c.timezone,
            end_time   = (a.end_time   AT TIME ZONE 'UTC') AT TIME ZONE c.timezone
        FROM clinics c
        WHERE c.id = a.clinic_id AND c.timezone <> 'UTC'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE appointments a
        SET start_time = (a.start_time AT TIME ZONE c.timezone) AT TIME ZONE 'UTC',
            end_time   = (a.end_time   AT TIME ZONE c.timezone) AT TIME ZONE 'UTC'
        FROM clinics c
        WHERE c.id = a.clinic_id AND c.timezone <> 'UTC'
        """
    )

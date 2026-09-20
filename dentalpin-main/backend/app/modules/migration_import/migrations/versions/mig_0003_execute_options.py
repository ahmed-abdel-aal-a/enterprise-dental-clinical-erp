"""migration_import — add ``execute_options`` JSONB to import jobs.

Adds a single JSONB column on ``migration_import_jobs`` so the execute
phase can persist operator-tunable knobs (currently the professional
filter sliders) without spawning a new column per option.

Stays on the dedicated ``migration_import`` Alembic branch — never
threads through another module's revision chain so uninstall stays
clean (issue #56).

Revision ID: mig_0003
Revises: mig_0002
Create Date: 2026-05-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "mig_0003"
down_revision: str | None = "mig_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "migration_import_jobs",
        sa.Column("execute_options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("migration_import_jobs", "execute_options")

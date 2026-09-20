"""staff_tasks: initial schema.

Tables:
    - ``staff_tasks`` — one handoff/task row on the clinic's board.

Only FKs to core tables (clinics, users), so the revision needs no
``depends_on``. Lives on its own Alembic branch (``staff_tasks``) per
ADR 0002.

Revision ID: stk_0001
Revises: 0001
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "stk_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("staff_tasks",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "staff_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="normal"),
        sa.Column("assignee_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_tasks_clinic_id", "staff_tasks", ["clinic_id"])
    op.create_index("ix_staff_tasks_status", "staff_tasks", ["status"])
    op.create_index("ix_staff_tasks_assignee_id", "staff_tasks", ["assignee_id"])


def downgrade() -> None:
    op.drop_table("staff_tasks")

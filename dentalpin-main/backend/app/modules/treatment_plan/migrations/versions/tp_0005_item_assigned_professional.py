"""Add assigned_professional_id to planned_treatment_items.

Each line in a treatment plan can now record which professional is
responsible for performing that specific treatment. Backfills existing
items with the doctor of their parent plan so the data starts in a
consistent state.

Revision ID: tp_0005
Revises: tp_0004
Create Date: 2026-05-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "tp_0005"
down_revision: str | None = "tp_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "planned_treatment_items",
        sa.Column("assigned_professional_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_planned_items_assigned_professional",
        "planned_treatment_items",
        "users",
        ["assigned_professional_id"],
        ["id"],
    )
    op.create_index(
        "ix_planned_treatment_items_assigned_professional_id",
        "planned_treatment_items",
        ["assigned_professional_id"],
    )
    op.create_index(
        "idx_planned_items_plan_professional",
        "planned_treatment_items",
        ["treatment_plan_id", "assigned_professional_id"],
    )

    # Backfill from the parent plan's assigned_professional_id. We populate
    # every item (including completed ones) so historical queries have a
    # consistent value; the UI keeps showing completed_by for completed items.
    op.execute(
        """
        UPDATE planned_treatment_items pti
           SET assigned_professional_id = tp.assigned_professional_id
          FROM treatment_plans tp
         WHERE pti.treatment_plan_id = tp.id
           AND pti.assigned_professional_id IS NULL
           AND tp.assigned_professional_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index(
        "idx_planned_items_plan_professional",
        table_name="planned_treatment_items",
    )
    op.drop_index(
        "ix_planned_treatment_items_assigned_professional_id",
        table_name="planned_treatment_items",
    )
    op.drop_constraint(
        "fk_planned_items_assigned_professional",
        "planned_treatment_items",
        type_="foreignkey",
    )
    op.drop_column("planned_treatment_items", "assigned_professional_id")

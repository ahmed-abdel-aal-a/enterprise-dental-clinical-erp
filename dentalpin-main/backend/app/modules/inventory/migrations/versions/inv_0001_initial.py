"""inventory: initial schema — stock list with low-stock thresholds.

Tables:
    - ``inventory_items`` — one row per stock item, with
      ``stock_quantity`` guarded by a CHECK (>= 0) so concurrent
      adjustments can never drive it negative (PR #153 post-mortem,
      roadmap #220).

Only FKs to core tables (clinics, users), so no ``depends_on``. Lives on
its own Alembic branch (``inventory``) per ADR 0002.

Revision ID: inv_0001
Revises: 0001
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "inv_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("inventory",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("stock_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("min_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_inventory_items_stock_non_negative"),
    )
    op.create_index("ix_inventory_items_clinic_id", "inventory_items", ["clinic_id"])
    op.create_index("ix_inventory_items_category", "inventory_items", ["category"])


def downgrade() -> None:
    op.drop_table("inventory_items")

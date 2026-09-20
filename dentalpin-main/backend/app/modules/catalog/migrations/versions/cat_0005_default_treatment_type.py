"""Add is_default_for_type to treatment_catalog_items.

Revision ID: cat_0005
Revises: cat_0004
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cat_0005"
down_revision: str | None = "cat_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use inspect or catch to make upgrade idempotent if column already exists in DB
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("treatment_catalog_items")]
    if "is_default_for_type" not in columns:
        op.add_column(
            "treatment_catalog_items",
            sa.Column("is_default_for_type", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )

    indexes = [ix["name"] for ix in inspector.get_indexes("treatment_catalog_items")]
    if "idx_catalog_items_default_type" not in indexes:
        op.create_index(
            "idx_catalog_items_default_type",
            "treatment_catalog_items",
            ["clinic_id", "is_default_for_type"]
        )


def downgrade() -> None:
    op.drop_index("idx_catalog_items_default_type", table_name="treatment_catalog_items")
    op.drop_column("treatment_catalog_items", "is_default_for_type")

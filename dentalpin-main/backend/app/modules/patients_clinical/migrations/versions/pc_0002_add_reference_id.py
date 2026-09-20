"""patients_clinical: nullable reference_id for the four history tables.

Loose (FK-less) link to the optional medical_reference module's lookup
rows — a plain nullable UUID so this module stays fully standalone when
medical_reference is uninstalled; existing rows simply keep matching by
name only.

Revision ID: pc_0002
Revises: pc_0001
Create Date: 2026-08-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pc_0002"
down_revision: str | None = "pc_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "patients_clinical_allergy",
    "patients_clinical_medication",
    "patients_clinical_systemic_disease",
    "patients_clinical_surgical_history",
)


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("reference_id", sa.UUID(), nullable=True))


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_column(table, "reference_id")

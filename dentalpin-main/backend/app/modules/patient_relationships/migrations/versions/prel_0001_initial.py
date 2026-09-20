"""patient_relationships: initial schema.

Tables:
    - ``patient_relationships_exemption_status`` — 1:1 insurance exemption status (APCI/ALD).
    - ``patient_relationships`` — directed patient-to-patient link.

Both FK to ``patients.id`` / ``clinics.id``. clinics.id is core (created
by "0001" itself, always available). patients.id is NOT core, though
-- patients lives on its own migration chain (pat_0001 -> pat_0002 ->
pat_0003) with no branch_labels of its own, so it is easy to assume
it's "part of core" the way clinics is. It isn't: depends_on is needed
so a fresh install orders patients' chain before this FK — same pattern
as recalls/rec_0001 (depends_on for its patients/agenda FKs).

Lives on its own Alembic branch (``patient_relationships``) per ADR 0002.

Revision ID: prel_0001
Revises: 0001
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "prel_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("patient_relationships",)
depends_on: str | Sequence[str] | None = ("pat_0003",)


def upgrade() -> None:
    op.create_table(
        "patient_relationships_exemption_status",
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("exemption_type", sa.String(length=20), nullable=False, server_default="none"),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        "ix_patient_relationships_exemption_status_clinic_id",
        "patient_relationships_exemption_status",
        ["clinic_id"],
    )
    op.create_index(
        "ix_patient_relationships_exemption_status_exemption_type",
        "patient_relationships_exemption_status",
        ["exemption_type"],
    )

    op.create_table(
        "patient_relationships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("related_patient_id", sa.UUID(), nullable=False),
        sa.Column("relationship_type", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "patient_id", "related_patient_id", name="uq_patient_relationships_pair"
        ),
    )
    op.create_index("ix_patient_relationships_clinic_id", "patient_relationships", ["clinic_id"])
    op.create_index("ix_patient_relationships_patient_id", "patient_relationships", ["patient_id"])
    op.create_index(
        "ix_patient_relationships_related_patient_id",
        "patient_relationships",
        ["related_patient_id"],
    )


def downgrade() -> None:
    op.drop_table("patient_relationships")
    op.drop_table("patient_relationships_exemption_status")

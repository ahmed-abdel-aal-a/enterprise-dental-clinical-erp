"""migration_import — add mapping_decisions for operator-overridable catalog mapping.

Adds ``migration_import_mapping_decisions`` so the operator can review
and override the catalog mapper's automatic proposals between the
preview and execute phases of a job. See ``models.MappingDecision`` for
the column-level contract.

Stays on the dedicated ``migration_import`` Alembic branch — never
threads through another module's revision chain so uninstall stays
clean (issue #56).

Revision ID: mig_0002
Revises: mig_0001
Create Date: 2026-05-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "mig_0002"
down_revision: str | None = "mig_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "migration_import_mapping_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
            server_default="treatment_catalog_item",
        ),
        sa.Column("canonical_uuid", sa.String(length=36), nullable=False),
        sa.Column("source_label", sa.String(length=255), nullable=False),
        sa.Column("source_code", sa.String(length=50), nullable=True),
        sa.Column("source_tipo_odg", sa.Integer(), nullable=True),
        sa.Column("proposed_action", sa.String(length=20), nullable=False),
        sa.Column("proposed_target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("proposed_target_label", sa.String(length=255), nullable=True),
        sa.Column("proposed_target_category_key", sa.String(length=50), nullable=True),
        sa.Column("proposed_score", sa.Float(), nullable=True),
        sa.Column(
            "operator_action",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("operator_target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operator_target_category_key", sa.String(length=50), nullable=True),
        sa.Column("operator_notes", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["migration_import_jobs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_id",
            "entity_type",
            "canonical_uuid",
            name="uq_migration_mapping_decision",
        ),
    )
    op.create_index(
        "ix_migration_import_mapping_decisions_job_id",
        "migration_import_mapping_decisions",
        ["job_id"],
    )
    op.create_index(
        "ix_migration_import_mapping_decisions_clinic_id",
        "migration_import_mapping_decisions",
        ["clinic_id"],
    )
    op.create_index(
        "ix_migration_mapping_decision_action",
        "migration_import_mapping_decisions",
        ["job_id", "operator_action"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_migration_mapping_decision_action",
        table_name="migration_import_mapping_decisions",
    )
    op.drop_index(
        "ix_migration_import_mapping_decisions_clinic_id",
        table_name="migration_import_mapping_decisions",
    )
    op.drop_index(
        "ix_migration_import_mapping_decisions_job_id",
        table_name="migration_import_mapping_decisions",
    )
    op.drop_table("migration_import_mapping_decisions")

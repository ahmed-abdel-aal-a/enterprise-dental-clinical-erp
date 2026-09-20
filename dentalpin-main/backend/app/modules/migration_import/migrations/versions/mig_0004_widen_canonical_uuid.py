"""migration_import — widen ``source_canonical_uuid`` to fit sidecar suffixes.

The ``appointment_note`` sidecar registers a derived canonical of
shape ``<uuid>:note`` (~41 chars), which overflowed the original
``VARCHAR(36)`` column and aborted every appointment savepoint —
turning every appointment migration into a ``mapper.failed`` error.

VARCHAR(64) leaves room for future ``<uuid>:<short_suffix>``
sidecars without another migration.

Revision ID: mig_0004
Revises: mig_0003
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "mig_0004"
down_revision: str | None = "mig_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "migration_import_entity_mappings",
        "source_canonical_uuid",
        existing_type=sa.String(length=36),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "migration_import_entity_mappings",
        "source_canonical_uuid",
        existing_type=sa.String(length=64),
        type_=sa.String(length=36),
        existing_nullable=False,
    )

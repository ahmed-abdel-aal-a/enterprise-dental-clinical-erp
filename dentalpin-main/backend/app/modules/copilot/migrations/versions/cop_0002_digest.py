"""copilot module — morning digest opt-in settings.

Revision ID: cop_0002
Revises: cop_0001
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "cop_0002"
down_revision: str | None = "cop_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "copilot_settings",
        sa.Column("digest_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "copilot_settings",
        sa.Column("digest_hour", sa.SmallInteger(), nullable=False, server_default="8"),
    )
    op.add_column(
        "copilot_settings",
        sa.Column(
            "digest_recipient_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("copilot_settings", "digest_recipient_user_id")
    op.drop_column("copilot_settings", "digest_hour")
    op.drop_column("copilot_settings", "digest_enabled")

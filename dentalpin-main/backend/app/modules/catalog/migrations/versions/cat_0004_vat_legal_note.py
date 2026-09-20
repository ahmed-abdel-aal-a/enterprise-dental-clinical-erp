"""Add vat_types.legal_note — statutory clause printed on invoices.

Spanish dental care is VAT-exempt under art. 20.Uno.5º LIVA and
accountants expect the exemption clause on every invoice (#204). The
clause lives on the VAT type so the country preset seeds it and other
countries can reuse the mechanism.

Backfills the seeded Spanish exempt type for existing ES clinics
(rate 0, system-seeded "Exento") — other clinics keep NULL.

Revision ID: cat_0004
Revises: cat_0003
Create Date: 2026-08-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "cat_0004"
down_revision: str | None = "cat_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ES_EXEMPT_NOTE = "Operación exenta de IVA según el art. 20.Uno.5º de la Ley 37/1992"


def upgrade() -> None:
    op.add_column("vat_types", sa.Column("legal_note", sa.String(length=300), nullable=True))
    # Existing Spanish-preset clinics: their seeded exempt type predates the
    # column. Match on the clinic's country plus the seeded row's shape so
    # generic-preset clinics (identical "Exento" names, different country)
    # are left untouched.
    op.execute(
        sa.text(
            """
            UPDATE vat_types
            SET legal_note = :note
            WHERE legal_note IS NULL
              AND rate = 0
              AND is_system = TRUE
              AND names->>'es' = 'Exento'
              AND clinic_id IN (
                  SELECT id FROM clinics WHERE UPPER(settings->>'country') = 'ES'
              )
            """
        ).bindparams(note=_ES_EXEMPT_NOTE)
    )


def downgrade() -> None:
    op.drop_column("vat_types", "legal_note")

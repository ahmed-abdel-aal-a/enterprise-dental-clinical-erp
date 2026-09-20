"""VAT statutory clauses flow from the seed to the invoice PDF (#204).

- the "es" preset seeds the exemption clause on the exempt VAT type;
  the generic preset does not
- ``vat_legal_notes_for_invoice`` returns the distinct clauses of the
  invoice's lines
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.service import InvoiceService, vat_legal_notes_for_invoice
from app.modules.catalog.models import VatType
from app.modules.catalog.seed import ES_EXEMPT_LEGAL_NOTE, _ensure_vat_types
from tests.modules.billing.helpers import accepted_budget, invoice_from_budget


@pytest.mark.asyncio
async def test_es_preset_seeds_exemption_clause(
    db_session: AsyncSession, budget_clinic_setup: dict
) -> None:
    from uuid import UUID

    clinic_id = UUID(budget_clinic_setup["clinic_id"])
    # The fixture pre-creates a rate-0 type, so seeding is idempotent over
    # it; wipe it to observe a fresh "es" seed.
    for vat in (
        (await db_session.execute(select(VatType).where(VatType.clinic_id == clinic_id)))
        .scalars()
        .all()
    ):
        await db_session.delete(vat)
    await db_session.flush()

    vat_map, created = await _ensure_vat_types(db_session, clinic_id, "es")
    assert created == 3
    exempt = await db_session.get(VatType, vat_map["exempt"])
    assert exempt is not None and exempt.legal_note == ES_EXEMPT_LEGAL_NOTE
    standard = await db_session.get(VatType, vat_map["standard"])
    assert standard is not None and standard.legal_note is None


@pytest.mark.asyncio
async def test_generic_preset_has_no_spanish_clause(
    db_session: AsyncSession, budget_clinic_setup: dict
) -> None:
    from uuid import UUID

    clinic_id = UUID(budget_clinic_setup["clinic_id"])
    for vat in (
        (await db_session.execute(select(VatType).where(VatType.clinic_id == clinic_id)))
        .scalars()
        .all()
    ):
        await db_session.delete(vat)
    await db_session.flush()

    vat_map, created = await _ensure_vat_types(db_session, clinic_id, "generic")
    assert created == 1
    exempt = await db_session.get(VatType, vat_map["exempt"])
    assert exempt is not None and exempt.legal_note is None


@pytest.mark.asyncio
async def test_invoice_collects_distinct_line_clauses(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    budget_clinic_setup: dict,
) -> None:
    from uuid import UUID

    clinic_id = UUID(budget_clinic_setup["clinic_id"])
    # Give the fixture's exempt VAT type the Spanish clause.
    vat = await db_session.get(VatType, UUID(budget_clinic_setup["vat_type_id"]))
    assert vat is not None
    vat.legal_note = ES_EXEMPT_LEGAL_NOTE
    await db_session.commit()

    budget_id, item_id = await accepted_budget(client, auth_headers, budget_clinic_setup)
    invoice_data = await invoice_from_budget(client, auth_headers, budget_id, item_id)

    invoice = await InvoiceService.get_invoice(
        db_session, clinic_id, UUID(invoice_data["id"]), include_items=True
    )
    assert invoice is not None
    notes = await vat_legal_notes_for_invoice(db_session, clinic_id, invoice)
    assert notes == [ES_EXEMPT_LEGAL_NOTE]

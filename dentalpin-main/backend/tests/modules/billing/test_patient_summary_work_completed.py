"""Patient billing summary derives "work completed" from fully invoiced quotes.

The ``completed`` budget status was removed in 2026-04, which left the
``work_completed`` KPI permanently at 0 (issue #242). Financial closure on
the budget axis is now "fully invoiced": every line's ``invoiced_quantity``
has reached its ``quantity``. ``work_in_progress`` is the complement, so the
two KPIs partition the accepted total.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.modules.billing.helpers import accepted_budget, invoice_from_budget


async def _patient_summary(client: AsyncClient, auth_headers: dict, patient_id: str) -> dict:
    r = await client.get(f"/api/v1/billing/patients/{patient_id}/summary", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]


@pytest.mark.asyncio
async def test_partially_invoiced_budget_counts_as_in_progress(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """An accepted quote with lines still to invoice is work in progress."""
    budget_id, item_id = await accepted_budget(
        client, auth_headers, budget_clinic_setup, quantity=2
    )
    await invoice_from_budget(client, auth_headers, budget_id, item_id, quantity=1)

    summary = await _patient_summary(client, auth_headers, budget_clinic_setup["patient_id"])
    assert Decimal(summary["work_in_progress"]) == Decimal("200.00")
    assert Decimal(summary["work_completed"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_fully_invoiced_budget_counts_as_completed(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """Once every line is fully invoiced the total moves to work completed."""
    budget_id, item_id = await accepted_budget(
        client, auth_headers, budget_clinic_setup, quantity=2
    )
    await invoice_from_budget(client, auth_headers, budget_id, item_id, quantity=1)
    await invoice_from_budget(client, auth_headers, budget_id, item_id, quantity=1)

    summary = await _patient_summary(client, auth_headers, budget_clinic_setup["patient_id"])
    assert Decimal(summary["work_in_progress"]) == Decimal("0.00")
    assert Decimal(summary["work_completed"]) == Decimal("200.00")


@pytest.mark.asyncio
async def test_draft_budget_counts_in_neither_kpi(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """Non-accepted quotes stay out of both work KPIs."""
    r = await client.post(
        "/api/v1/budget/budgets",
        json={"patient_id": budget_clinic_setup["patient_id"], "valid_from": "2024-01-01"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    budget_id = r.json()["data"]["id"]
    r = await client.post(
        f"/api/v1/budget/budgets/{budget_id}/items",
        json={"catalog_item_id": budget_clinic_setup["catalog_item_id"], "quantity": 1},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text

    summary = await _patient_summary(client, auth_headers, budget_clinic_setup["patient_id"])
    assert Decimal(summary["total_budgeted"]) == Decimal("100.00")
    assert Decimal(summary["work_in_progress"]) == Decimal("0.00")
    assert Decimal(summary["work_completed"]) == Decimal("0.00")

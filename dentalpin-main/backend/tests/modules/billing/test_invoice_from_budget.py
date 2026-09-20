"""Invoices created from an accepted quote carry its discounts (issue #167).

The quote's line discount and its prorated global discount are folded into
each invoice line (ex-tax); Verifactu derives BaseImponible per line, so an
invoice-level discount is never an option.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.modules.billing.helpers import accepted_budget, invoice_from_budget


@pytest.mark.asyncio
async def test_line_and_global_discounts_reach_the_invoice(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """100 → 80 (line 20%) → 72 (global 10%): stored as one absolute line discount of 28."""
    budget_id, item_id = await accepted_budget(
        client,
        auth_headers,
        budget_clinic_setup,
        line_discount={"discount_type": "percentage", "discount_value": 20},
        global_discount={"global_discount_type": "percentage", "global_discount_value": 10},
    )
    invoice = await invoice_from_budget(client, auth_headers, budget_id, item_id)
    line = invoice["items"][0]
    assert line["discount_type"] == "absolute"
    assert Decimal(line["discount_value"]) == Decimal("28.00")
    assert Decimal(line["line_discount"]) == Decimal("28.00")
    assert Decimal(line["line_total"]) == Decimal("72.00")
    assert Decimal(invoice["total"]) == Decimal("72.00")


@pytest.mark.asyncio
async def test_percentage_only_line_discount_is_kept_as_percentage(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    budget_id, item_id = await accepted_budget(
        client,
        auth_headers,
        budget_clinic_setup,
        line_discount={"discount_type": "percentage", "discount_value": 20},
    )
    invoice = await invoice_from_budget(client, auth_headers, budget_id, item_id)
    line = invoice["items"][0]
    assert line["discount_type"] == "percentage"
    assert Decimal(line["discount_value"]) == Decimal("20.00")
    assert Decimal(invoice["total"]) == Decimal("80.00")


@pytest.mark.asyncio
async def test_absolute_line_discount_prorated_on_partial_invoicing(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """Qty 2 with 30 € absolute discount, invoiced 1 unit → 15 € on that invoice, not 30."""
    budget_id, item_id = await accepted_budget(
        client,
        auth_headers,
        budget_clinic_setup,
        quantity=2,
        line_discount={"discount_type": "absolute", "discount_value": 30},
    )
    first = await invoice_from_budget(client, auth_headers, budget_id, item_id, quantity=1)
    assert Decimal(first["items"][0]["discount_value"]) == Decimal("15.00")
    assert Decimal(first["total"]) == Decimal("85.00")
    second = await invoice_from_budget(client, auth_headers, budget_id, item_id)
    assert Decimal(second["total"]) == Decimal("85.00")


@pytest.mark.asyncio
async def test_absolute_global_discount_is_prorated_and_never_negative(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """A global absolute discount larger than the quote is clamped: the line ends at 0, not below."""
    budget_id, item_id = await accepted_budget(
        client,
        auth_headers,
        budget_clinic_setup,
        global_discount={"global_discount_type": "absolute", "global_discount_value": 500},
    )
    invoice = await invoice_from_budget(client, auth_headers, budget_id, item_id)
    line = invoice["items"][0]
    assert Decimal(line["line_discount"]) == Decimal("100.00")
    assert Decimal(line["line_total"]) == Decimal("0.00")
    assert Decimal(invoice["total"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_no_discount_round_trips_untouched(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    budget_id, item_id = await accepted_budget(client, auth_headers, budget_clinic_setup)
    invoice = await invoice_from_budget(client, auth_headers, budget_id, item_id)
    line = invoice["items"][0]
    assert line["discount_type"] is None
    assert Decimal(invoice["total"]) == Decimal("100.00")


async def _invoiced_qty(client: AsyncClient, auth_headers: dict, budget_id: str) -> int:
    r = await client.get(f"/api/v1/budget/budgets/{budget_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]["items"][0]["invoiced_quantity"]


@pytest.mark.asyncio
async def test_void_delete_and_item_edits_release_quote_lines(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """invoiced_quantity follows the live invoice lines (issue #175)."""
    budget_id, item_id = await accepted_budget(
        client, auth_headers, budget_clinic_setup, quantity=3
    )
    h = auth_headers
    b = "/api/v1/billing/invoices"

    # Void a draft → line comes back.
    inv = await invoice_from_budget(client, h, budget_id, item_id, quantity=2)
    assert await _invoiced_qty(client, h, budget_id) == 2
    r = await client.post(f"{b}/{inv['id']}/void", headers=h)
    assert r.status_code == 200, r.text
    assert await _invoiced_qty(client, h, budget_id) == 0

    # Delete a draft → line comes back.
    inv = await invoice_from_budget(client, h, budget_id, item_id, quantity=2)
    r = await client.delete(f"{b}/{inv['id']}", headers=h)
    assert r.status_code == 204, r.text
    assert await _invoiced_qty(client, h, budget_id) == 0

    # Editing / deleting a draft line keeps the counter in sync.
    inv = await invoice_from_budget(client, h, budget_id, item_id, quantity=3)
    line_id = inv["items"][0]["id"]
    r = await client.put(f"{b}/{inv['id']}/items/{line_id}", json={"quantity": 1}, headers=h)
    assert r.status_code == 200, r.text
    assert await _invoiced_qty(client, h, budget_id) == 1
    r = await client.delete(f"{b}/{inv['id']}/items/{line_id}", headers=h)
    assert r.status_code == 204, r.text
    assert await _invoiced_qty(client, h, budget_id) == 0

    # The full quantity is available again.
    await invoice_from_budget(client, h, budget_id, item_id, quantity=3)
    assert await _invoiced_qty(client, h, budget_id) == 3
    r = await client.post(
        f"{b}/from-budget/{budget_id}", json={"items": [{"budget_item_id": item_id}]}, headers=h
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_credit_note_releases_quote_lines(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    budget_id, item_id = await accepted_budget(
        client, auth_headers, budget_clinic_setup, quantity=2
    )
    h = auth_headers
    b = "/api/v1/billing/invoices"

    r = await client.put(
        f"/api/v1/patients/{budget_clinic_setup['patient_id']}",
        json={"billing_tax_id": "12345678Z"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    for prefix, series_type in (("FAC", "invoice"), ("RECT", "credit_note")):
        r = await client.post(
            "/api/v1/billing/series",
            json={"prefix": prefix, "series_type": series_type, "is_default": True},
            headers=h,
        )
        assert r.status_code == 201, r.text

    inv = await invoice_from_budget(client, h, budget_id, item_id)
    r = await client.post(f"{b}/{inv['id']}/issue", json={}, headers=h)
    assert r.status_code == 200, r.text
    assert await _invoiced_qty(client, h, budget_id) == 2

    r = await client.post(f"{b}/{inv['id']}/credit-note", json={"reason": "error"}, headers=h)
    assert r.status_code == 201, r.text
    cn_id = r.json()["data"]["id"]
    assert await _invoiced_qty(client, h, budget_id) == 0

    # Dropping the draft credit note consumes the lines again.
    r = await client.delete(f"{b}/{cn_id}", headers=h)
    assert r.status_code == 204, r.text
    assert await _invoiced_qty(client, h, budget_id) == 2


@pytest.mark.asyncio
async def test_partial_invoices_with_global_discount_add_up_to_the_quote(
    client: AsyncClient, auth_headers: dict, budget_clinic_setup: dict
) -> None:
    """qty 2 with a 20 % line discount and a 10 % global: invoicing 1 + 1 must
    reproduce the quote's discount and total exactly (issue #181)."""
    budget_id, item_id = await accepted_budget(
        client,
        auth_headers,
        budget_clinic_setup,
        quantity=2,
        line_discount={"discount_type": "percentage", "discount_value": 20},
        global_discount={"global_discount_type": "percentage", "global_discount_value": 10},
    )
    quote = (await client.get(f"/api/v1/budget/budgets/{budget_id}", headers=auth_headers)).json()[
        "data"
    ]
    first = await invoice_from_budget(client, auth_headers, budget_id, item_id, quantity=1)
    second = await invoice_from_budget(client, auth_headers, budget_id, item_id, quantity=1)

    invoiced_discount = Decimal(first["total_discount"]) + Decimal(second["total_discount"])
    invoiced_total = Decimal(first["total"]) + Decimal(second["total"])
    assert invoiced_discount == Decimal(quote["total_discount"])  # 40 + 16
    assert invoiced_total == Decimal(quote["total"])  # 200 − 56

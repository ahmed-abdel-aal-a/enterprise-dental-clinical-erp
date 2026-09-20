"""Shared HTTP-level helpers for billing tests (quote → accept → invoice-from-budget)."""

from __future__ import annotations

from httpx import AsyncClient


async def accepted_budget(
    client: AsyncClient,
    auth_headers: dict,
    setup: dict,
    *,
    quantity: int = 1,
    line_discount: dict | None = None,
    global_discount: dict | None = None,
) -> tuple[str, str]:
    """Create → add one 100 € line → accept. Returns (budget_id, item_id)."""
    r = await client.post(
        "/api/v1/budget/budgets",
        json={
            "patient_id": setup["patient_id"],
            "valid_from": "2024-01-01",
            **(global_discount or {}),
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    budget_id = r.json()["data"]["id"]
    r = await client.post(
        f"/api/v1/budget/budgets/{budget_id}/items",
        json={
            "catalog_item_id": setup["catalog_item_id"],
            "quantity": quantity,
            **(line_discount or {}),
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    item_id = r.json()["data"]["id"]
    r = await client.post(
        f"/api/v1/budget/budgets/{budget_id}/accept",
        headers=auth_headers,
        json={"signature": {"signed_by_name": "Test", "relationship_to_patient": "patient"}},
    )
    assert r.status_code == 200, r.text
    return budget_id, item_id


async def invoice_from_budget(
    client: AsyncClient,
    auth_headers: dict,
    budget_id: str,
    item_id: str,
    quantity: int | None = None,
) -> dict:
    spec: dict = {"budget_item_id": item_id}
    if quantity is not None:
        spec["quantity"] = quantity
    r = await client.post(
        f"/api/v1/billing/invoices/from-budget/{budget_id}",
        json={"items": [spec]},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    invoice_id = r.json()["data"]["id"]
    r = await client.get(f"/api/v1/billing/invoices/{invoice_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]

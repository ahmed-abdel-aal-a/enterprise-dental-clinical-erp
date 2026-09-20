"""E-invoice retry is honest: no provider exists in v1, so always 409."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.india_gst.models import IndiaGstEinvoiceSubmission, IndiaGstSettings
from app.modules.patients.models import Patient


async def test_retry_returns_409_never_fabricates_success(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
):
    from app.modules.billing.models import Invoice
    from app.modules.patients.models import Patient

    user_id = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()["data"]["user"][
        "id"
    ]
    patient = Patient(
        id=uuid4(), clinic_id=india_gst_settings.clinic_id, first_name="A", last_name="B"
    )
    db_session.add(patient)
    await db_session.flush()
    invoice = Invoice(
        id=uuid4(),
        clinic_id=india_gst_settings.clinic_id,
        patient_id=patient.id,
        status="issued",
        billing_name="A B",
        created_by=user_id,
    )
    db_session.add(invoice)
    submission = IndiaGstEinvoiceSubmission(
        clinic_id=india_gst_settings.clinic_id, invoice_id=invoice.id, state="not_configured"
    )
    db_session.add(submission)
    await db_session.commit()

    r = await client.post(
        f"/api/v1/india_gst/invoices/{invoice.id}/einvoice/retry", headers=auth_headers
    )
    assert r.status_code == 409
    assert "provider" in r.json()["message"].lower()

    await db_session.refresh(submission)
    assert submission.state == "not_configured"


async def test_einvoice_applicability_based_on_turnover_threshold_not_invoice_amount(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    """E-invoice applicability is based on aggregate annual turnover
    (declared via turnover_threshold), NOT a single invoice's total.
    A small invoice with threshold set → not_configured.
    A large invoice without threshold → not_required."""
    from app.modules.catalog.models import (
        TreatmentCatalogItem,
        TreatmentCategory,
        VatType,
    )

    # Case 1: No turnover_threshold → not_required regardless of invoice amount
    assert india_gst_settings.turnover_threshold is None

    vat = VatType(clinic_id=india_gst_settings.clinic_id, names={"en": "GST 18%"}, rate=18.0)
    category = TreatmentCategory(
        clinic_id=india_gst_settings.clinic_id, key="einv-test", names={"en": "Test"}
    )
    db_session.add_all([vat, category])
    await db_session.flush()
    item = TreatmentCatalogItem(
        clinic_id=india_gst_settings.clinic_id,
        category_id=category.id,
        internal_code="EINV-01",
        names={"en": "Expensive crown"},
        default_price="100000.00",
        vat_type_id=vat.id,
    )
    db_session.add(item)
    await db_session.commit()

    r = await client.post(
        "/api/v1/billing/invoices", json={"patient_id": str(test_patient.id)}, headers=auth_headers
    )
    invoice_id = r.json()["data"]["id"]
    await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/items",
        json={
            "description": "Expensive crown",
            "catalog_item_id": str(item.id),
            "unit_price": "100000.00",
            "quantity": 1,
            "vat_type_id": str(vat.id),
        },
        headers=auth_headers,
    )
    await client.put(
        f"/api/v1/india_gst/invoices/{invoice_id}",
        json={"place_of_supply": "33"},
        headers=auth_headers,
    )
    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["compliance_data"]["IN"]["einvoice_state"] == "not_required"

    # Case 2: Set turnover_threshold → not_configured even for a tiny invoice
    india_gst_settings.turnover_threshold = Decimal("5000000.00")
    db_session.add(india_gst_settings)
    await db_session.commit()

    r = await client.post(
        "/api/v1/billing/invoices", json={"patient_id": str(test_patient.id)}, headers=auth_headers
    )
    invoice_id2 = r.json()["data"]["id"]
    await client.post(
        f"/api/v1/billing/invoices/{invoice_id2}/items",
        json={
            "description": "Cheap cleaning",
            "catalog_item_id": str(item.id),
            "unit_price": "100.00",
            "quantity": 1,
            "vat_type_id": str(vat.id),
        },
        headers=auth_headers,
    )
    await client.put(
        f"/api/v1/india_gst/invoices/{invoice_id2}",
        json={"place_of_supply": "33"},
        headers=auth_headers,
    )
    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id2}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["compliance_data"]["IN"]["einvoice_state"] == "not_configured"

"""Billing-party snapshot on issue (#206).

Drafts carry no billing data; ``issue()`` snapshots it from the patient.
A patient with a DNI/NIE but no explicit ``billing_tax_id`` must still be
invoiceable — the first invoice of a fresh clinic used to fail here.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, User
from app.modules.billing.models import Invoice, InvoiceItem, InvoiceSeries
from app.modules.patients.models import Patient


async def _patient(db: AsyncSession, clinic: Clinic, **fields) -> Patient:
    patient = Patient(
        id=uuid4(), clinic_id=clinic.id, first_name="Ana", last_name="Pérez", **fields
    )
    db.add(patient)
    await db.commit()
    return patient


async def _draft(db: AsyncSession, clinic: Clinic, patient: Patient) -> Invoice:
    user_id = (await db.execute(select(User))).scalars().first().id
    db.add(
        InvoiceSeries(
            id=uuid4(), clinic_id=clinic.id, prefix="FAC", series_type="invoice", is_default=True
        )
    )
    inv = Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        status="draft",
        subtotal=Decimal("60.00"),
        total=Decimal("60.00"),
        created_by=user_id,
    )
    db.add(inv)
    await db.flush()
    db.add(
        InvoiceItem(
            id=uuid4(),
            clinic_id=clinic.id,
            invoice_id=inv.id,
            description="Limpieza",
            unit_price=Decimal("60.00"),
            quantity=1,
            vat_rate=0.0,
            line_subtotal=Decimal("60.00"),
            line_tax=Decimal("0.00"),
            line_total=Decimal("60.00"),
            display_order=0,
        )
    )
    await db.commit()
    return inv


def test_effective_billing_fields_fall_back_to_identity() -> None:
    dni = Patient(
        first_name="Ana", last_name="Pérez", national_id="12345678Z", national_id_type="dni"
    )
    assert dni.effective_billing_name == "Ana Pérez"
    assert dni.effective_billing_tax_id == "12345678Z"
    assert dni.has_complete_billing_info is True

    passport = Patient(
        first_name="Ana", last_name="Pérez", national_id="X123", national_id_type="passport"
    )
    assert passport.effective_billing_tax_id is None
    assert passport.has_complete_billing_info is False

    explicit = Patient(
        first_name="Ana",
        last_name="Pérez",
        billing_name="Clínica SL",
        billing_tax_id="B1",
        national_id="X",
    )
    assert (explicit.effective_billing_name, explicit.effective_billing_tax_id) == (
        "Clínica SL",
        "B1",
    )


@pytest.mark.asyncio
async def test_issue_snapshots_dni_as_tax_id(
    client: AsyncClient, auth_headers: dict, test_clinic: Clinic, db_session: AsyncSession
) -> None:
    patient = await _patient(
        db_session, test_clinic, national_id="12345678Z", national_id_type="dni"
    )
    inv = await _draft(db_session, test_clinic, patient)

    resp = await client.post(
        f"/api/v1/billing/invoices/{inv.id}/issue", json={}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "issued"
    assert data["billing_name"] == "Ana Pérez"
    assert data["billing_tax_id"] == "12345678Z"


@pytest.mark.asyncio
async def test_issue_without_any_tax_id_is_rejected(
    client: AsyncClient, auth_headers: dict, test_clinic: Clinic, db_session: AsyncSession
) -> None:
    patient = await _patient(
        db_session, test_clinic, national_id="X123", national_id_type="passport"
    )
    inv = await _draft(db_session, test_clinic, patient)

    resp = await client.post(
        f"/api/v1/billing/invoices/{inv.id}/issue", json={}, headers=auth_headers
    )
    assert resp.status_code == 400, resp.text
    assert "incomplete billing data" in resp.json()["message"]


@pytest.mark.asyncio
async def test_create_patient_accepts_national_id(
    client: AsyncClient, auth_headers: dict, test_clinic: Clinic
) -> None:
    resp = await client.post(
        "/api/v1/patients",
        json={"first_name": "Ana", "last_name": "Pérez", "national_id": "12345678Z"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["has_complete_billing_info"] is True

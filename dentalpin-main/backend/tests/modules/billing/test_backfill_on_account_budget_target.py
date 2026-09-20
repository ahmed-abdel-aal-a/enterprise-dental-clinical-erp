"""Backfill script for #180's legacy on_account rows.

Before #178, ``apply_payment_to_invoice`` always created an
``on_account`` allocation, even for invoices born from a budget — the
"Budget payments" card only sums ``target_type == "budget"`` rows, so
those legacy collections stayed invisible on the quote even though
they were already correctly imputed to the invoice (#180). This shape
can no longer be produced through the current API (#178 fixed the
write path), so these tests seed the pre-#178 row shape directly, the
same way ``backend/scripts/backfill_on_account_budget_target.py``'s
own docstring describes it.
"""

from __future__ import annotations

import importlib.util
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, User
from app.modules.billing.models import Invoice, InvoiceItem, InvoicePayment, InvoiceSeries
from app.modules.budget.models import Budget
from app.modules.patients.models import Patient
from app.modules.payments.models import Payment, PaymentAllocation

SCRIPT_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "backfill_on_account_budget_target.py"
)
_spec = importlib.util.spec_from_file_location("backfill_on_account_budget_target", SCRIPT_PATH)
backfill = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(backfill)


async def _user_id(db: AsyncSession):
    return (await db.execute(select(User))).scalars().first().id


async def _budget(db: AsyncSession, clinic: Clinic, patient: Patient, total: str) -> Budget:
    budget = Budget(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        budget_number=f"PRES-{uuid4().hex[:6]}",
        status="accepted",
        valid_from=date.today(),
        created_by=await _user_id(db),
        total=Decimal(total),
    )
    db.add(budget)
    await db.commit()
    return budget


async def _issued_invoice(
    db: AsyncSession, clinic: Clinic, patient: Patient, total: str, budget: Budget | None
) -> Invoice:
    if not (
        await db.execute(select(InvoiceSeries.id).where(InvoiceSeries.clinic_id == clinic.id))
    ).first():
        db.add(
            InvoiceSeries(
                id=uuid4(),
                clinic_id=clinic.id,
                prefix="FAC",
                series_type="invoice",
                is_default=True,
            )
        )
    inv = Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        status="issued",
        billing_name="Cliente Test",
        billing_tax_id="B12345678",
        subtotal=Decimal(total),
        total=Decimal(total),
        issue_date=date.today(),
        created_by=await _user_id(db),
        budget_id=budget.id if budget else None,
    )
    db.add(inv)
    await db.flush()
    db.add(
        InvoiceItem(
            id=uuid4(),
            clinic_id=clinic.id,
            invoice_id=inv.id,
            description="Servicio",
            unit_price=Decimal(total),
            quantity=1,
            vat_rate=0.0,
            line_subtotal=Decimal(total),
            line_tax=Decimal("0.00"),
            line_total=Decimal(total),
            display_order=0,
        )
    )
    await db.commit()
    return inv


async def _legacy_on_account_payment(
    db: AsyncSession,
    clinic: Clinic,
    patient: Patient,
    amount: str,
    *,
    linked_invoices: list[tuple[Invoice, str]],
) -> Payment:
    """Seed the pre-#178 shape: one on_account allocation + manual
    InvoicePayment link(s), exactly like the old unconditional branch
    of ``apply_payment_to_invoice`` used to create.
    """
    actor = await _user_id(db)
    payment = Payment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        amount=Decimal(amount),
        currency="EUR",
        method="cash",
        payment_date=date.today(),
        recorded_by=actor,
    )
    db.add(payment)
    await db.flush()
    db.add(
        PaymentAllocation(
            id=uuid4(),
            clinic_id=clinic.id,
            payment_id=payment.id,
            target_type="on_account",
            budget_id=None,
            amount=Decimal(amount),
            created_by=actor,
        )
    )
    for invoice, link_amount in linked_invoices:
        db.add(
            InvoicePayment(
                id=uuid4(),
                clinic_id=clinic.id,
                invoice_id=invoice.id,
                payment_id=payment.id,
                amount=Decimal(link_amount),
                created_by=actor,
            )
        )
    await db.commit()
    return payment


async def _budget_allocation_total(db: AsyncSession, clinic: Clinic, budget: Budget) -> Decimal:
    result = await db.execute(
        select(PaymentAllocation).where(
            PaymentAllocation.clinic_id == clinic.id,
            PaymentAllocation.target_type == "budget",
            PaymentAllocation.budget_id == budget.id,
        )
    )
    return sum((a.amount for a in result.scalars()), Decimal("0"))


async def _allocation_for(db: AsyncSession, payment: Payment) -> PaymentAllocation:
    result = await db.execute(
        select(PaymentAllocation).where(PaymentAllocation.payment_id == payment.id)
    )
    return result.scalars().one()


@pytest.mark.asyncio
async def test_dry_run_touches_nothing(
    test_clinic: Clinic, test_patient: Patient, db_session: AsyncSession
) -> None:
    budget = await _budget(db_session, test_clinic, test_patient, "100.00")
    inv = await _issued_invoice(db_session, test_clinic, test_patient, "100.00", budget)
    payment = await _legacy_on_account_payment(
        db_session, test_clinic, test_patient, "100.00", linked_invoices=[(inv, "100.00")]
    )

    await backfill.main(apply=False)

    refreshed = await _allocation_for(db_session, payment)
    assert refreshed.target_type == "on_account"
    assert await _budget_allocation_total(db_session, test_clinic, budget) == Decimal("0")


@pytest.mark.asyncio
async def test_apply_reclassifies_deterministic_legacy_row(
    test_clinic: Clinic, test_patient: Patient, db_session: AsyncSession
) -> None:
    budget = await _budget(db_session, test_clinic, test_patient, "100.00")
    inv = await _issued_invoice(db_session, test_clinic, test_patient, "100.00", budget)
    payment = await _legacy_on_account_payment(
        db_session, test_clinic, test_patient, "100.00", linked_invoices=[(inv, "100.00")]
    )

    await backfill.main(apply=True)

    refreshed = await _allocation_for(db_session, payment)
    assert (refreshed.target_type, refreshed.budget_id) == ("budget", budget.id)
    assert await _budget_allocation_total(db_session, test_clinic, budget) == Decimal("100.00")

    # No-op on the pre-existing link: still exactly one row, same amount —
    # reconcile_payment recognised the objective already matched current.
    links = (
        (
            await db_session.execute(
                select(InvoicePayment).where(InvoicePayment.payment_id == payment.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(links) == 1
    assert links[0].amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_apply_leaves_multi_budget_split_untouched(
    test_clinic: Clinic, test_patient: Patient, db_session: AsyncSession
) -> None:
    budget_a = await _budget(db_session, test_clinic, test_patient, "60.00")
    budget_b = await _budget(db_session, test_clinic, test_patient, "40.00")
    inv_a = await _issued_invoice(db_session, test_clinic, test_patient, "60.00", budget_a)
    inv_b = await _issued_invoice(db_session, test_clinic, test_patient, "40.00", budget_b)
    payment = await _legacy_on_account_payment(
        db_session,
        test_clinic,
        test_patient,
        "100.00",
        linked_invoices=[(inv_a, "60.00"), (inv_b, "40.00")],
    )

    await backfill.main(apply=True)

    refreshed = await _allocation_for(db_session, payment)
    assert refreshed.target_type == "on_account"


@pytest.mark.asyncio
async def test_apply_leaves_genuine_unassigned_credit_untouched(
    test_clinic: Clinic, test_patient: Patient, db_session: AsyncSession
) -> None:
    payment = await _legacy_on_account_payment(
        db_session, test_clinic, test_patient, "75.00", linked_invoices=[]
    )

    await backfill.main(apply=True)

    refreshed = await _allocation_for(db_session, payment)
    assert refreshed.target_type == "on_account"


@pytest.mark.asyncio
async def test_apply_leaves_multi_allocation_payment_untouched(
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
    capsys: pytest.CaptureFixture,
) -> None:
    """A payment split across on_account + budget in one shot is not the
    legacy shape — ``reallocate_payment`` replaces *all* of a payment's
    allocation rows, so touching it would risk dropping the other one.
    Must be flagged and skipped, not guessed at.

    Note: ``reallocate_payment``'s own "new allocations must sum to
    payment.amount" invariant would *also* reject this particular case
    (our proposed single-row replacement can never sum to the full
    payment amount when a sibling row exists) — so the end state alone
    doesn't prove *this script's* guard is what fired. Assert on the
    printed reasoning too, so a future edit that weakens/removes the
    guard is still caught even if it happens to stay accidentally safe.
    """
    budget = await _budget(db_session, test_clinic, test_patient, "100.00")
    inv = await _issued_invoice(db_session, test_clinic, test_patient, "100.00", budget)
    actor = await _user_id(db_session)
    payment = Payment(
        id=uuid4(),
        clinic_id=test_clinic.id,
        patient_id=test_patient.id,
        amount=Decimal("100.00"),
        currency="EUR",
        method="cash",
        payment_date=date.today(),
        recorded_by=actor,
    )
    db_session.add(payment)
    await db_session.flush()
    db_session.add(
        PaymentAllocation(
            id=uuid4(),
            clinic_id=test_clinic.id,
            payment_id=payment.id,
            target_type="on_account",
            budget_id=None,
            amount=Decimal("40.00"),
            created_by=actor,
        )
    )
    db_session.add(
        PaymentAllocation(
            id=uuid4(),
            clinic_id=test_clinic.id,
            payment_id=payment.id,
            target_type="budget",
            budget_id=budget.id,
            amount=Decimal("60.00"),
            created_by=actor,
        )
    )
    db_session.add(
        InvoicePayment(
            id=uuid4(),
            clinic_id=test_clinic.id,
            invoice_id=inv.id,
            payment_id=payment.id,
            amount=Decimal("40.00"),
            created_by=actor,
        )
    )
    await db_session.commit()

    await backfill.main(apply=True)

    out = capsys.readouterr().out
    assert f"AMBIGUOUS payment={payment.id}" in out, (
        "the multi-row guard must be what skips this payment, not an "
        "accidental catch further downstream"
    )
    assert "reallocate failed" not in out

    rows = (
        (
            await db_session.execute(
                select(PaymentAllocation).where(PaymentAllocation.payment_id == payment.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2, "the other allocation row must survive untouched"
    assert {(r.target_type, r.amount) for r in rows} == {
        ("on_account", Decimal("40.00")),
        ("budget", Decimal("60.00")),
    }


@pytest.mark.asyncio
async def test_apply_is_idempotent(
    test_clinic: Clinic, test_patient: Patient, db_session: AsyncSession
) -> None:
    budget = await _budget(db_session, test_clinic, test_patient, "100.00")
    inv = await _issued_invoice(db_session, test_clinic, test_patient, "100.00", budget)
    await _legacy_on_account_payment(
        db_session, test_clinic, test_patient, "100.00", linked_invoices=[(inv, "100.00")]
    )

    await backfill.main(apply=True)
    await backfill.main(apply=True)  # re-run: nothing left to reclassify

    assert await _budget_allocation_total(db_session, test_clinic, budget) == Decimal("100.00")

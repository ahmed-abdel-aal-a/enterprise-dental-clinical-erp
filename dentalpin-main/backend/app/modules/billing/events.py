"""Billing event handlers.

Transactional (ADR 0019 — declare ``db`` and run inside the payments
module's transaction; a failure rolls the payment back):

* ``payment.allocated`` — reconcile ``invoice_payments`` with the
  payment's budget allocations (issue #178, ``payment_bridge``).
* ``payment.refunded`` — recompute the status of any invoices whose
  ``invoice_payments`` link the refunded Payment (``paid → partial`` /
  ``partial → issued``).

Own-session:

* ``clinic.created`` — create the default invoice / credit-note series so
  the first invoice can be issued without visiting settings.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker

from .models import Invoice, InvoicePayment
from .service import InvoiceSeriesService
from .workflow import InvoiceWorkflowService

logger = logging.getLogger(__name__)


def _uuid(value: Any) -> UUID | None:
    try:
        return UUID(str(value)) if value else None
    except (ValueError, TypeError):
        return None


async def on_payment_allocated(data: dict[str, Any], *, db: AsyncSession) -> None:
    """A payment's allocations were created or replaced — mirror them
    onto this budget's invoices (see ``payment_bridge.reconcile_payment``).

    Runs for every allocation row (budget *and* on_account) because a
    reallocation away from a budget must unlink too; the reconcile is
    idempotent so repeated calls per payment are harmless.
    """
    from .payment_bridge import reconcile_payment

    clinic_id, payment_id, actor_id = (
        _uuid(data.get("clinic_id")),
        _uuid(data.get("payment_id")),
        _uuid(data.get("actor_id")),
    )
    if clinic_id is None or payment_id is None or actor_id is None:
        raise ValueError("payment.allocated payload missing clinic_id/payment_id/actor_id")
    context = data.get("context") or {}
    await reconcile_payment(
        db,
        clinic_id=clinic_id,
        payment_id=payment_id,
        actor_id=actor_id,
        prefer_invoice_id=_uuid(context.get("prefer_invoice_id")),
    )


async def on_payment_refunded(data: dict[str, Any], *, db: AsyncSession) -> None:
    """Refund happened upstream — re-evaluate any invoice the payment
    was imputed against, in the same transaction.

    Idempotent: ``recalc_invoice_status`` is a no-op when status
    matches reality.
    """
    clinic_id, payment_id = _uuid(data.get("clinic_id")), _uuid(data.get("payment_id"))
    if clinic_id is None or payment_id is None:
        raise ValueError("payment.refunded payload missing clinic_id/payment_id")

    invoice_ids_q = await db.execute(
        select(InvoicePayment.invoice_id)
        .where(InvoicePayment.payment_id == payment_id, InvoicePayment.clinic_id == clinic_id)
        .distinct()
    )
    invoice_ids = [row[0] for row in invoice_ids_q.all()]
    if not invoice_ids:
        return

    invoices_q = await db.execute(select(Invoice).where(Invoice.id.in_(invoice_ids)))
    for invoice in invoices_q.scalars():
        actor_id = _uuid(data.get("refunded_by")) or invoice.created_by
        await InvoiceWorkflowService.recalc_invoice_status(db, invoice, actor_id=actor_id)


async def on_clinic_created(data: dict[str, Any]) -> None:
    """Seed ``FAC`` (invoice) + ``RECT`` (credit note) default series.

    Idempotent: skipped when the clinic already has any series.

    own-session (issue #183): ``clinic.created`` is published after
    ``POST /auth/setup`` commits, so there is nothing uncommitted to miss —
    and seeding must not stretch the signup transaction.
    """
    clinic_id_raw = data.get("clinic_id")
    if not clinic_id_raw:
        return
    try:
        clinic_id = UUID(str(clinic_id_raw))
    except (ValueError, TypeError):
        return

    async with async_session_maker() as db:
        try:
            existing = await InvoiceSeriesService.list_series(db, clinic_id, active_only=False)
            if existing:
                return
            await InvoiceSeriesService.create_series(
                db,
                clinic_id,
                {"prefix": "FAC", "series_type": "invoice", "is_default": True},
            )
            await InvoiceSeriesService.create_series(
                db,
                clinic_id,
                {"prefix": "RECT", "series_type": "credit_note", "is_default": True},
            )
            await db.commit()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("billing.on_clinic_created failed: %s", exc, exc_info=True)
            await db.rollback()

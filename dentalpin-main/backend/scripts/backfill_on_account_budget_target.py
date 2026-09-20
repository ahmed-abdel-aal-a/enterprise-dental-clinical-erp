"""One-shot backfill: reclassify legacy ``on_account`` allocations that
are actually budget collections into ``target_type="budget"`` (#180).

Why this exists: before #178, ``apply_payment_to_invoice`` always
created an ``on_account`` allocation plus a manual ``InvoicePayment``
link, even when the invoice belonged to a budget. #178 added the
``from_budget`` branch that creates a real ``budget`` allocation going
forward, but rows recorded before that fix are still stored as
``on_account`` — invisible to the "Budget payments" card
(``PaymentReadService.total_collected_for_budget`` and siblings only
sum ``target_type == "budget"`` rows), even though the money is
already correctly imputed to that budget's invoice.

What it does: for every payment whose *entire* allocation set is a
single ``on_account`` row, whose ``InvoicePayment`` links point to
exactly one budget's (non-deleted) invoice(s), and whose linked total
matches the allocation amount exactly — reclassify it via
``payments.workflow.reallocate_payment``, the same function the
"Asignar a presupuesto…" button uses. That function is transactional,
audit-logs the change (``PaymentHistory``), and fires
``payment.allocated``, which ``billing.payment_bridge.reconcile_payment``
consumes in the same transaction (ADR-0019) to reconcile
``invoice_payments`` — a no-op here, since the link this
reclassification targets already exists with the exact matching
amount. Only the allocation's own ``target_type``/``budget_id`` flips;
no invoice status or balance changes.

A payment with more than one allocation row is *not* the legacy shape
(``reallocate_payment`` replaces a payment's whole allocation set, so
touching it would risk dropping its other rows) — flagged for manual
review, never touched. Same for a payment with no matching link at
all (genuine unassigned credit, ADR-0010 — already correct) — silently
skipped, not even flagged. Same for a link spanning more than one
budget, or a linked total that doesn't exactly match the allocation
amount — flagged for manual review.

Dry-run by default: prints every allocation it would reclassify
(payment id, clinic id, budget id, invoice id(s), amount), touches
nothing. ``--apply`` to execute.

Idempotent: once reclassified, a row's ``target_type`` is no longer
``on_account`` so a re-run skips it.

Usage::

    docker-compose exec backend python scripts/backfill_on_account_budget_target.py
    docker-compose exec backend python scripts/backfill_on_account_budget_target.py --apply

Run once after deploying this backfill. Can be re-run safely.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from uuid import UUID

# Allow running the script directly via `python backend/scripts/...`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

# Force SQLAlchemy to resolve every cross-module relationship by
# loading all module models the same way the app does at startup.
from app.core.plugins.loader import register_discovered  # noqa: E402
from app.database import async_session_maker  # noqa: E402

for _module in register_discovered():
    _module.get_models()

from app.core.auth.models import ClinicMembership, User  # noqa: E402
from app.modules.billing.models import Invoice, InvoicePayment  # noqa: E402
from app.modules.payments.models import Payment, PaymentAllocation  # noqa: E402
from app.modules.payments.service import PaymentService  # noqa: E402
from app.modules.payments.workflow import PaymentWorkflowError, reallocate_payment  # noqa: E402


async def _admin_for_clinic(db, clinic_id: UUID) -> User | None:
    result = await db.execute(
        select(User)
        .join(ClinicMembership, ClinicMembership.user_id == User.id)
        .where(
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.role == "admin",
            User.is_active.is_(True),
        )
        .order_by(User.created_at)
        .limit(1)
    )
    return result.scalars().first()


async def main(apply: bool) -> int:
    reclassified = 0
    skipped_no_link = 0
    flagged_ambiguous = 0
    skipped_no_admin = 0

    async with async_session_maker() as db:
        payment_ids_q = await db.execute(
            select(PaymentAllocation.payment_id)
            .where(PaymentAllocation.target_type == "on_account")
            .distinct()
        )
        payment_ids = [row[0] for row in payment_ids_q.all()]

        admin_cache: dict[UUID, User | None] = {}

        for payment_id in payment_ids:
            clinic_id_q = await db.execute(
                select(Payment.clinic_id).where(Payment.id == payment_id)
            )
            clinic_id = clinic_id_q.scalar_one()

            payment = await PaymentService.get(db, clinic_id, payment_id)
            if payment is None:
                continue

            # Not the legacy shape: reallocate_payment replaces a payment's
            # *entire* allocation set, so touching a multi-row payment risks
            # dropping its other rows. Flag instead of guessing.
            if len(payment.allocations) != 1 or payment.allocations[0].target_type != "on_account":
                flagged_ambiguous += 1
                print(
                    f"AMBIGUOUS payment={payment_id} clinic={clinic_id}: "
                    f"{len(payment.allocations)} allocation row(s), not a single on_account row "
                    "— skipped, needs manual review"
                )
                continue

            alloc = payment.allocations[0]

            links_q = await db.execute(
                select(InvoicePayment.amount, Invoice.budget_id, Invoice.id)
                .join(Invoice, Invoice.id == InvoicePayment.invoice_id)
                .where(
                    InvoicePayment.payment_id == payment_id,
                    Invoice.budget_id.is_not(None),
                    Invoice.deleted_at.is_(None),
                )
            )
            rows = links_q.all()
            if not rows:
                # Genuine unassigned credit (ADR-0010) — correct as-is.
                skipped_no_link += 1
                continue

            by_budget: dict[UUID, list] = defaultdict(list)
            for amount, budget_id, invoice_id in rows:
                by_budget[budget_id].append((amount, invoice_id))

            if len(by_budget) != 1:
                flagged_ambiguous += 1
                print(
                    f"AMBIGUOUS payment={payment_id} clinic={clinic_id} amount={alloc.amount}: "
                    f"linked to {len(by_budget)} different budgets "
                    f"({sorted(str(b) for b in by_budget)}) — skipped, needs manual review"
                )
                continue

            (budget_id, entries) = next(iter(by_budget.items()))
            linked_total = sum((amount for amount, _ in entries), Decimal("0"))
            if linked_total != alloc.amount:
                flagged_ambiguous += 1
                invoice_ids = sorted(str(iid) for _, iid in entries)
                print(
                    f"AMBIGUOUS payment={payment_id} clinic={clinic_id} amount={alloc.amount}: "
                    f"linked total {linked_total} to budget {budget_id} "
                    f"(invoices {invoice_ids}) does not match — skipped, needs manual review"
                )
                continue

            invoice_ids = sorted(str(iid) for _, iid in entries)
            print(
                f"{'APPLY' if apply else 'DRY-RUN'} payment={payment_id} clinic={clinic_id} "
                f"amount={alloc.amount} -> budget={budget_id} (invoices {invoice_ids})"
            )

            if not apply:
                continue

            if clinic_id not in admin_cache:
                admin_cache[clinic_id] = await _admin_for_clinic(db, clinic_id)
            admin = admin_cache[clinic_id]
            if admin is None:
                skipped_no_admin += 1
                print(f"  SKIPPED: no active admin found for clinic {clinic_id}")
                continue

            try:
                await reallocate_payment(
                    db,
                    clinic_id=clinic_id,
                    payment=payment,
                    new_allocations=[
                        {
                            # A real ``uuid.UUID``, not ``str(budget_id)``:
                            # ``_validate_allocations_for_clinic`` builds its
                            # found-budgets dict keyed by ``Budget.id``
                            # (asyncpg's native UUID type, which hashes/
                            # compares equal to stdlib ``uuid.UUID`` — the
                            # type Pydantic always hands it via the API) and
                            # looks entries up by this value directly. A
                            # plain ``str`` never hashes equal to a UUID, so
                            # the lookup would silently miss an existing
                            # budget every time.
                            "target_type": "budget",
                            "target_id": UUID(str(budget_id)),
                            "amount": alloc.amount,
                        }
                    ],
                    changed_by=admin.id,
                )
            except PaymentWorkflowError as exc:
                print(f"  SKIPPED: reallocate failed: {exc}")
                continue
            reclassified += 1

        if apply:
            await db.commit()
        else:
            await db.rollback()

    print(
        f"backfill_on_account_budget_target: reclassified={reclassified} "
        f"skipped_no_link={skipped_no_link} flagged_ambiguous={flagged_ambiguous} "
        f"skipped_no_admin={skipped_no_admin}"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually reclassify eligible rows (default: dry-run, prints only).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(asyncio.run(main(args.apply)))

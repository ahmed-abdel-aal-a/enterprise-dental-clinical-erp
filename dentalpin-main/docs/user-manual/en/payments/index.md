---
module: payments
last_verified_commit: b1b82f5
---

# Payments

The payments module runs the clinic's **real cash flow**: every
payment received from a patient, split across budgets and *on
account*, with their refunds, plus a per-patient ledger. It also
feeds the financial reports under the `reports` module.

It is a **patient-centric** module, not invoice-centric. A single
payment can cover several budgets, sit partially *on account*, or
spread across different treatments. Billing links payments when a
formal invoice has to be issued — never the other way around.

## Screens

- [Payment list](./screens/payments.md) — every payment with
  filters, allocations, and a refund shortcut.
- [Payment reports](./screens/reports_payments.md) — KPIs, trends,
  payment methods, professionals, aging, refunds.

## Quick reference

| Action | Required permission |
|--------|---------------------|
| View list, patient ledger, and allocations | `payments.record.read` |
| Record a payment or reallocate it | `payments.record.write` |
| Issue a refund | `payments.record.refund` (admin/dentist by default) |
| See the payment reports | `payments.reports.read` |

## Related modules

- **Budgets** — every payment can be allocated across one or more
  patient budgets. The budget page shows a *Paid / Outstanding*
  sidebar card with the breakdown.
- **Patients** — the *Administration* tab on the patient record
  includes the patient ledger (KPIs + timeline + refund row menu).
- **Billing** — billing depends on payments, not the reverse. An
  invoice may link to one or more payments (`invoice_payments` lives
  inside the `billing` module).
- **Odontogram and treatment plans** — feed *earned* data
  (`PatientEarnedEntry`) to payments via the
  `odontogram.treatment.performed` and
  `treatment_plan.treatment_completed` events. Reports use it for
  aging analysis.
- **Reports** — the `/reports` page links to `/reports/payments`
  whenever the payments module is installed.

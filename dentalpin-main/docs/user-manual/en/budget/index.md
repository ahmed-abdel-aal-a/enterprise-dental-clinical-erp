---
module: budget
last_verified_commit: b1b82f5
---

# Budgets

The budget module manages the patient's dental quotes: catalog
items, discounts, VAT, versioning, signature, PDF, and a clear
`draft → sent → accepted → completed` workflow (with branches to
*rejected*, *expired*, or *cancelled*).

It bridges the clinician's treatment plan and invoicing: once the
patient accepts a budget, you can issue the invoice from the
`billing` module and collect it through `payments`.

## Screens

- [Budget list](./screens/budgets.md) — search, filter by status /
  payment / validity, sort, and open budgets.
- [Budget detail](./screens/budgets_id.md) — edit lines, totals,
  send, accept/reject, renegotiate, see the signature, and download
  the PDF.
- [New budget](./screens/budgets_new.md) — create a budget from
  scratch or from a treatment plan.
- [Public patient acceptance](./screens/p_budget_token.md) — public
  view for the patient (no app session) with 2FA verification,
  accept or reject from a phone.

## Quick reference

| Action | Required permission |
|--------|---------------------|
| View budgets and download PDFs | `budget.read` |
| Create, edit, send, accept (in-clinic requires extra permission) | `budget.write` |
| Delete a budget | `budget.admin` |
| Renegotiate (create a new version without losing history) | `budget.renegotiate` |
| Accept by signing in-clinic (tablet) | `budget.accept_in_clinic` |

## Related modules

- **Patients / Catalog / Odontogram** — direct dependencies. Line
  items reference the catalog and, optionally, teeth and surfaces
  on the odontogram.
- **Treatment plans** — a plan can generate budgets and stays in
  sync when treatments are added or removed. Communication is
  event-driven (snapshot payloads), never via imports.
- **Billing** — from an accepted budget you can jump into *Create
  invoice from this budget*.
- **Payments** — the detail sidebar shows collected / outstanding
  and a *Charge* button (contributed by the payments module).
- **Notifications** — `budget.sent`, `budget.accepted`,
  `budget.rejected`, `budget.expired`, `budget.viewed`, and
  `budget.reminder_sent` are published for future outreach.

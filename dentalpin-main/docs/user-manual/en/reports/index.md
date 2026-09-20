---
module: reports
last_verified_commit: b1b82f5
---

# Reports

The clinic's reporting hub. `reports` is a **read-only** module
that aggregates data from the business modules (billing, budgets,
agenda) into dashboards. Other modules can add their own reports to
the dashboard through the `reports.categories` slot — for example,
`payments` contributes the payments report (see
[payment reports](../payments/screens/reports_payments.md)).

## Screens

- [Reports dashboard](./screens/reports.md) — entry point with one
  card per report family.
- [Billing](./screens/reports_billing.md) — totals invoiced, by
  series, by payment method, evolution.
- [Budgets](./screens/reports_budgets.md) — conversion, time in
  each state, rejection / closure reasons.
- [Agenda and occupancy](./screens/reports_scheduling.md) — busy
  hours, no-shows, cancellations, professional mix.

## Quick reference

| Action | Required permission |
|--------|---------------------|
| View the dashboard | any of the three permissions below |
| See billing reports | `reports.billing.read` |
| See budget reports | `reports.budgets.read` |
| See agenda reports | `reports.scheduling.read` |
| See payment reports (contributed by `payments`) | `payments.reports.read` |

## Related modules

- **Billing, budgets, agenda** — sources of the aggregated reports.
- **Payments** — contributes the payments card via the
  `reports.categories` slot.
- **Catalog, patients** — references and enrichments in aggregated
  rows (treatment category, patient, professional).

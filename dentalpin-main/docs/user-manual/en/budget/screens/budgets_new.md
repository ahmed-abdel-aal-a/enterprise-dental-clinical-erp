---
module: budget
screen: create
route: /budgets/new
related_endpoints:
  - DELETE /api/v1/budget/budgets/{budget_id}
  - DELETE /api/v1/budget/budgets/{budget_id}/items/{item_id}
  - GET /api/v1/budget/budgets
  - GET /api/v1/budget/budgets/{budget_id}
  - GET /api/v1/budget/budgets/{budget_id}/history
  - GET /api/v1/budget/budgets/{budget_id}/pdf
  - GET /api/v1/budget/budgets/{budget_id}/pdf/preview
  - GET /api/v1/budget/budgets/{budget_id}/pdf/signed
  - GET /api/v1/budget/budgets/{budget_id}/signature
  - GET /api/v1/budget/budgets/{budget_id}/versions
  - POST /api/v1/budget/budgets
  - POST /api/v1/budget/budgets/{budget_id}/accept
  - POST /api/v1/budget/budgets/{budget_id}/accept-in-clinic
  - POST /api/v1/budget/budgets/{budget_id}/cancel
  - POST /api/v1/budget/budgets/{budget_id}/duplicate
  - POST /api/v1/budget/budgets/{budget_id}/items
  - POST /api/v1/budget/budgets/{budget_id}/reject
  - POST /api/v1/budget/budgets/{budget_id}/renegotiate
  - POST /api/v1/budget/budgets/{budget_id}/resend
  - POST /api/v1/budget/budgets/{budget_id}/send
  - POST /api/v1/budget/budgets/{budget_id}/send-reminder
  - POST /api/v1/budget/budgets/{budget_id}/set-public-code
  - POST /api/v1/budget/budgets/{budget_id}/unlock-public
  - PUT /api/v1/budget/budgets/{budget_id}
  - PUT /api/v1/budget/budgets/{budget_id}/items/{item_id}
related_permissions:
  - budget.read
  - budget.write
related_paths:
  - backend/app/modules/budget/frontend/pages/budgets/new.vue
  - backend/app/modules/budget/router.py
  - backend/app/modules/treatment_plan/frontend/components/budget/NewBudgetPlanHint.vue
last_verified_commit: 7a1637d
---

# New quote

Form to create a quote **without a treatment plan**. On save it is born
in `draft` and the [detail](./budgets_id.md) opens, where lines are
added.

## At a glance

- **Header only.** Pick the patient, validity and notes here. Lines
  (catalog items, tooth, discounts, VAT) are added on the detail page
  after saving.
- **If the patient already has a treatment plan** in `draft` or
  `pending` without a quote, the form says so with a link to the plan:
  a plan's quote is generated **from the plan** (on confirm) so both
  stay linked and in sync. A quote created here is never linked to the
  plan.
- **Automatic numbering.** The number (`PRES-YYYY-####`) is assigned on
  save; not editable.
- **Validity.** `valid_from` defaults to today; `valid_until` is left
  empty (no expiry) unless you fill it in.

## Create a quote

> Requires `budget.write`.

1. Select the patient (coming from their record, cancel takes you
   back there).
2. If the "plan without quote" notice shows, click **Open plan** and
   generate the quote from there. Continue only when the quote belongs
   to no plan.
3. Adjust validity and notes (internal or patient-facing).
4. **Create and add items**. The detail opens in `draft` to add lines,
   send or sign.

## Create from a treatment plan

> Requires `treatment_plan.plans.confirm`.

On the plan, click **Confirm**: a linked `draft` quote is created with
the plan's treatments as lines. From then on the lines are managed from
the plan (see [quote detail](./budgets_id.md#edit-lines)).

## Permissions

| What you see / can do | Permission |
|-----------------------|------------|
| Create the quote | `budget.write` |
| See the "plan without quote" notice | `treatment_plan.plans.read` |

## Troubleshooting

- **The patient selector is empty.** You lack `patients.read`.
- **No notice although the patient has a plan.** Only `draft`/`pending`
  plans without a quote are flagged; a confirmed plan already has its
  quote on its own detail page.

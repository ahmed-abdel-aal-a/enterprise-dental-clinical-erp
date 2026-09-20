---
module: billing
screen: edit
route: /invoices/[id]/edit
related_endpoints:
  - DELETE /api/v1/billing/invoices/{invoice_id}/items/{item_id}
  - GET /api/v1/billing/invoices/{invoice_id}
  - GET /api/v1/billing/series
  - GET /api/v1/billing/settings
  - PATCH /api/v1/billing/invoices/{invoice_id}/billing-party
  - POST /api/v1/billing/invoices/{invoice_id}/items
  - PUT /api/v1/billing/invoices/{invoice_id}
  - PUT /api/v1/billing/invoices/{invoice_id}/items/{item_id}
related_permissions:
  - billing.read
  - billing.write
related_paths:
  - backend/app/modules/billing/frontend/pages/invoices/[id]/edit.vue
  - backend/app/modules/billing/router.py
last_verified_commit: b1b82f5
---

# Edit invoice draft

Form to edit an invoice draft. **Only available when the invoice
is in `draft`.** Issued invoices are not editable — you have to
void and re-issue, or issue a credit note.

## At a glance

- **Valid state:** `draft`. Any other state redirects to the
  [detail](./invoices_id.md) and shows the data read-only.
- **Receiver (payer).** Defaults to the patient. Click *Different
  payer* (PATCH `billing-party`) to point to a third party
  (company, insurer, family member) — the invoice is issued in
  the alternate payer's name.
- **Line items.** Add, edit, delete lines. Each line references a
  catalog item with description, quantity, unit price, discount,
  and VAT (snapshot of the catalog at the time the invoice was
  created).
- **Invoice series.** Not picked here: the active series assigns a
  number on issue. To use a different series, change the active
  one under *Settings → Invoice series*.

## Edit an invoice

> Requires `billing.write`.

1. Change discount, quantity, VAT, or add lines.
2. If the payer is not the patient, click *Different payer* and
   fill in the third-party legal data.
3. **Save**. The invoice stays in `draft`. To issue it, return to
   the [detail](./invoices_id.md) and click **Issue**.

## Permissions

| What you see / can do | Permission |
|-----------------------|------------|
| Load the form | `billing.read` |
| Edit lines and receiver data | `billing.write` |

## Troubleshooting

- **This screen redirects to the detail.** The invoice is no
  longer in `draft`. Only drafts can be edited.
- **Cannot add an item.** Check the item is active in the clinic's
  catalog and that you have `catalog.read`.
- **Total doesn't update when changing VAT.** Save so the server
  recomputes; the frontend shows a live result but the source of
  truth is the backend response.

---
module: expenses
screen: index
route: /expenses
related_endpoints:
  - GET /api/v1/expenses
  - GET /api/v1/expenses/monthly-totals
  - POST /api/v1/expenses
  - DELETE /api/v1/expenses/{expense_id}
related_permissions:
  - expenses.read
  - expenses.write
related_paths:
  - backend/app/modules/expenses/frontend/pages/expenses/index.vue
last_verified_commit: 3d0fc1d1
---

# Expense list

Fixed and recurring office cost tracking — rent, utilities, salaries,
supplies, equipment, insurance, maintenance, and other.

## Permissions

- The module is **admin-only out of the box**; clinics can grant
  `expenses.read` / `expenses.write` to other roles from the module
  admin UI.
- `expenses.read` — view the list and monthly totals.
- `expenses.write` — add and delete expenses.

## What this screen does

- **Filter** the list by category.
- **Add expense** — opens a modal for category, amount, date, and an
  optional description.
- **Monthly totals** — one badge per category for the current month.
- **Delete** per row behind `expenses.write`, with a confirmation
  dialog before anything is removed.
- **Pagination** — server-side, 20 rows per page.


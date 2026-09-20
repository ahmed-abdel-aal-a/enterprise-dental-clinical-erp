---
module: expenses
last_verified_commit: 3d0fc1d1
---

# Expenses

Fixed and recurring office cost tracking for the clinic: rent,
utilities, salaries, supplies, equipment, insurance, maintenance and
other. Each expense carries a date and optional description; a monthly
summary aggregates totals per category.

**Sensitive by default**: only `admin` sees the module initially (rent
and salaries are payroll-adjacent). The clinic can grant
`expenses.read` / `expenses.write` to other roles from the module admin
UI.

## Screens

- [Expense list](./screens/index.md): category filter, expense
  creation, monthly per-category totals and delete with confirmation.

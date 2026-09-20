---
module: expenses
last_verified_commit: 3d0fc1d1
---

# expenses — events

The module emits and consumes **no events**.

Expense rows are static accounting facts (amount + date + category);
nothing else in the tree needs to react to their lifecycle
asynchronously, and there is no denormalized state to keep in sync — so
there is nothing to transact under ADR 0019. If a future module needs to
react (e.g. accounting_export picking expenses into a ledger), add an
`EventType.EXPENSE_*` constant plus a transactional publisher at that
point.

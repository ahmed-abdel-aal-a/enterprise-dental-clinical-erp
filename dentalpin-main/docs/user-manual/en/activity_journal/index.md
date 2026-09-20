---
module: activity_journal
last_verified_commit: 03f4c5f1
---

# Activity log

Append-only staff activity journal: every subscribed module event
(appointments, budgets, invoices, payments, patients, recalls,
treatments, lab orders…) is recorded automatically with its actor,
patient, source entity and full payload.

**Sensitive by default**: only `admin` sees the module initially — the
log records which staff member did what. The clinic can grant
`activity_journal.read` to other roles from the module admin UI.
Entries can never be edited or deleted.

## Screens

- [Activity log](./screens/journal.md): event-type and date filters,
  pagination, per-row payload viewer.

---
module: activity_journal
screen: journal
route: /journal
related_endpoints:
  - GET /api/v1/activity_journal
  - GET /api/v1/activity_journal/{entry_id}
related_permissions:
  - activity_journal.read
related_paths:
  - backend/app/modules/activity_journal/frontend/pages/journal/index.vue
last_verified_commit: 169054a
---

# Activity log

Read-only list of everything the journal recorded, newest first. Each
row shows when it happened, which event produced it, who performed it
(a dash means the source event carried no user attribution), the
affected patient — as a link to their record — and the event namespace
(source). User and patient names are resolved on screen; when a name
cannot be resolved (deleted record, or you lack permission to read it)
a short id is shown instead.

## What you can do

- **Filter by event type** — pick one of the recorded event types from
  the select (e.g. `appointment.scheduled`, `budget.sent`).
- **Filter by date range** — restrict to a `From` / `To` window.
- **Paginate** — 20 rows per page via the pagination bar.
- **Inspect a payload** — use the eye button on a row to open a
  read-only view of the exact data the event carried.

Entries cannot be edited, deleted or created manually: they are written
automatically inside the transaction of the operation they describe, so
the log is always consistent with what actually happened.

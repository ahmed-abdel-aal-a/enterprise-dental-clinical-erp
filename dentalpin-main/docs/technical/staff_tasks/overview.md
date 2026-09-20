---
module: staff_tasks
last_verified_commit: e4146c9b
---

# staff_tasks — overview

The clinic's **staff handoff board**: internal tasks and handoff notes
between team members — "call patient X back about their quote",
"prepare implant kit for room 2", "order more gloves" — tracked from
`open` through `claimed` to `done`, with `cancelled` as an escape hatch.

## What it is

Clinic-scoped CRUD over a flat `StaffTask` list plus a guarded status
state machine:

```
open ──▶ claimed ──▶ done
  │          │
  └──▶ cancelled ◀┘        done is terminal; cancelled can reopen.
```

- Claiming an unassigned task assigns the claimer (router passes the
  authenticated user).
- Marking `done` stamps `completed_at`.
- Illegal transitions return `422`.

`priority` (`low|normal|high`) and `due_date` help the board sort what
matters first.

## Events

Emits `staff_task.created` and `staff_task.status_changed`
(`EventType.STAFF_TASK_*`), published transactionally per ADR 0019 —
inside the creating/updating transaction with the publisher's session.
No bundled subscribers.

## Data model

`staff_tasks` — `id`, `clinic_id`, `title`, `details` (nullable),
`status`, `priority`, `assignee_id` (nullable FK `users.id`),
`created_by` (nullable FK `users.id`), `due_date` (nullable),
`completed_at` (nullable), timestamps.

FKs point only at core tables, so the migration needs no `depends_on`.

## Dependencies

`manifest.depends = []` — fully standalone.

## Tenancy

Every read, write, delete and agent tool filters by the caller's
`clinic_id`; cross-clinic access surfaces as 404.

## Lifecycle

`installable=True`, `auto_install=False` (activated from the module
admin UI), `removable=True`. Own Alembic branch (`staff_tasks`) rooted
on core `"0001"`. Uninstall round-trip covered by
`test_uninstall_roundtrip.py`.

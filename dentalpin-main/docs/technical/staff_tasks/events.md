---
module: staff_tasks
last_verified_commit: e4146c9b
---

# staff_tasks — events

## Emitted

### `staff_task.created`

Published when a task is created. Constant:
`EventType.STAFF_TASK_CREATED`. Payload:

- `clinic_id`
- `task_id`
- `status` (always `"open"` here)
- `priority`
- `assignee_id` (nullable)
- `due_date` (nullable, ISO date)

### `staff_task.status_changed`

Published when PATCH changes a task's status through the guarded state
machine (`open → claimed → done`, `cancelled` escape hatch). Constant:
`EventType.STAFF_TASK_STATUS_CHANGED`. Same payload as above.

## Transaction model

Both events are published **inside** the creating/updating transaction —
after the row flush, before the caller's commit — passing the
publisher's session (`db=`) per ADR 0019, so any future transactional
subscriber sees the row and rolls back with it.

The module ships no subscribers of its own.

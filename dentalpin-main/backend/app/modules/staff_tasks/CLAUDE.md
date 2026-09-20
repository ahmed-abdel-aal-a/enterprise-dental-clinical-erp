# staff_tasks module

The clinic's staff handoff board — internal tasks and handoff notes
between team members ("call patient X back", "prepare implant kit for
room 2"), tracked through a guarded status lifecycle.

## Public API

Routes mounted at `/api/v1/staff_tasks/`.

- `GET    /staff_tasks`               — list; filters: `task_status`, `assignee_id`, `due_before` (all typed, incl. `date`); `staff_tasks.read`
- `GET    /staff_tasks/{id}`          — detail; `staff_tasks.read`
- `POST   /staff_tasks`               — create (201); `staff_tasks.write`
- `PATCH  /staff_tasks/{id}`          — edit / status transition (422 on illegal move); `staff_tasks.write`
- `DELETE /staff_tasks/{id}`          — delete (204); `staff_tasks.write`

## Dependencies

`manifest.depends = []` — standalone. FKs point only at core tables
(`clinics`, `users`), so the migration declares no `depends_on`.

## Permissions

`staff_tasks.read`, `staff_tasks.write`. Default grants: whole team
read+write — the board is collaboration infrastructure and holds no
sensitive data (same breadth precedent as patient_relationships).

## Status machine

```
open ──▶ claimed ──▶ done
  │          │
  └──▶ cancelled ◀┘        done is terminal; cancelled can reopen.
```

Claiming an unassigned task assigns the claimer. `done` stamps
`completed_at`. Illegal transitions raise 422.

## Tools exposed

| Tool | Category | Wraps | Permission |
|---|---|---|---|
| `list_staff_tasks` | READ | `StaffTaskService.list_tasks` | `staff_tasks.read` |
| `create_staff_task` | WRITE | `StaffTaskService.create_task` | `staff_tasks.write` |
| `update_staff_task_status` | WRITE | `StaffTaskService.update_task` | `staff_tasks.write` |

Agent-initiated tasks set `created_by = null` (AgentContext carries no
user identity); ids are returned as native UUIDs for jsonify.

## Events emitted

- `staff_task.created` (`EventType.STAFF_TASK_CREATED`)
- `staff_task.status_changed` (`EventType.STAFF_TASK_STATUS_CHANGED`)

Both published transactionally per ADR 0019: after flush, before the
caller's commit, with the publisher's session as `db=`.

## Events consumed

None.

## Lifecycle

- `installable=True`, `auto_install=False` (ships inactive, activated
  from the module admin UI), `removable=True`.
- Migrations on the `staff_tasks` Alembic branch rooted on core `0001`.
- `tests/modules/staff_tasks/test_uninstall_roundtrip.py` covers the
  branch-scoped downgrade/upgrade round trip (branch-relative `@-1`
  walk).

## CHANGELOG

See `./CHANGELOG.md`.
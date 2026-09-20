---
module: staff_tasks
last_verified_commit: e4146c9b
---

# staff_tasks — permissions

Namespaced by the registry from the module's `get_permissions()`.

| Permission | Gates | Endpoints |
|------------|-------|-----------|
| `staff_tasks.read` | View the handoff board | `GET /api/v1/staff_tasks/`, `GET /api/v1/staff_tasks/{task_id}` |
| `staff_tasks.write` | Create, claim/update status, edit, delete tasks | `POST /api/v1/staff_tasks/`, `PATCH …/{task_id}`, `DELETE …/{task_id}` |

Default role mapping: **the whole team participates** — a handoff board
only works if everyone can read and write it (same breadth precedent as
`patient_relationships`; this module holds no sensitive data):

| Role | Permissions |
|------|-------------|
| `admin` | all (`*`) |
| `dentist` | read, write |
| `hygienist` | read, write |
| `assistant` | read, write |
| `receptionist` | read, write |

Agent tools reuse the same two permission strings.

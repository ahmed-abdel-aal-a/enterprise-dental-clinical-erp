---
module: staff_tasks
screen: tasks
route: /tasks
related_endpoints:
  - GET /api/v1/staff_tasks/
  - POST /api/v1/staff_tasks/
  - PATCH /api/v1/staff_tasks/{task_id}
  - DELETE /api/v1/staff_tasks/{task_id}
related_permissions:
  - staff_tasks.read
  - staff_tasks.write
related_paths:
  - backend/app/modules/staff_tasks/router.py
  - backend/app/modules/staff_tasks/frontend/pages/tasks/index.vue
last_verified_commit: c536b1f0
---

# Staff task board

## What this screen does

- **Filter** by status (All / Open / Claimed / Done / Cancelled).
- **New task** — modal with title, optional details, priority
  (Low / Normal / High) and an optional due date.
- **Task details** show as a second line under the title; hover for the
  full text.
- **Assigned to** column shows who has each task.
- **Claim and close inline** — each row's status selector only offers
  the legal next moves; claiming an unassigned task assigns you, and
  marking it **Done** stamps the completion time. Re-opening a claimed
  task puts it back up for grabs.
- **Overdue** open tasks show their due date in red.
- **Delete** with a confirmation dialog.
- **Pagination** — server-side, 20 rows per page.

## Statuses

`Open → Claimed → Done`, with `Cancelled` as an escape hatch. `Done` is
terminal (the selector becomes a badge). An illegal move returns `422`
and shows an error toast.

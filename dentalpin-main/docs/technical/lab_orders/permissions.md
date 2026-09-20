---
module: lab_orders
last_verified_commit: c9c20493
---

# lab_orders — permissions

| Permission | Gates | Endpoints |
|---|---|---|
| `lab_orders.read` | View lab orders | `GET /api/v1/lab_orders/`, `GET /api/v1/lab_orders/{id}` |
| `lab_orders.write` | Create/update lab orders (cancel via status; no hard delete) | `POST`, `PATCH` under `/api/v1/lab_orders/` |

Default role mapping:

| Role | Permissions |
|---|---|
| `admin` | all (`*`) |
| `dentist` | read, write |
| `hygienist` | read only |
| `assistant` | read, write |
| `receptionist` | read, write |

---
module: lab_orders
last_verified_commit: c9c20493
---

# lab_orders — events

## Emitted

### `lab_order.status_changed`

Published when PATCH changes an order's status (the same update
auto-stamps `received_date` on `received`). Constant:
`EventType.LAB_ORDER_STATUS_CHANGED`. Payload:

- `clinic_id`
- `order_id`
- `patient_id`
- `status`
- `work_type`
- `tooth_reference`

The module ships no subscriber. Optional modules may consume the event without importing `lab_orders` directly.

## Transaction model

The module ships no event handlers, so it has no handler-side ADR 0019
obligations. Publisher-side: the status-change event is published
**inside** the update transaction — after the row flush, before the
caller's commit — passing the publisher's session (`db=`) so any future
transactional subscriber sees the updated row and rolls back with it.


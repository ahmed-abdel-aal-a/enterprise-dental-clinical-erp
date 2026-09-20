---
module: inventory
last_verified_commit: 47983b05
---

# inventory — events

## Emitted

### `inventory.low_stock`

Fired once per **not-low → low crossing**: when an item is created
already at/below its threshold, or when the first update/adjustment
crosses it. Repeated adjustments while still low do not re-fire.
Constant: `EventType.INVENTORY_STOCK_LOW`. Payload:

- `clinic_id`
- `item_id`
- `name`
- `category`
- `stock_quantity` (float)
- `min_quantity` (float)

## Transaction model

Published **inside** the creating/updating transaction — after flush,
before the caller's commit — with the publisher's session (`db=`) per
ADR 0019, so a future transactional subscriber (notifications,
procurement) sees the row and rolls back with it.

The module ships no subscribers of its own. A future procurement module
(#226 chain) subscribes without importing `inventory`.

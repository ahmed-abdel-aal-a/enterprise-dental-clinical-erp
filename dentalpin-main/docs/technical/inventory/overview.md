---
module: inventory
last_verified_commit: 47983b05
---

# inventory — overview

Standalone **stock list with low-stock alerts** (roadmap #220, base
version): flat per-item quantities with minimum thresholds, atomic
stock adjustments guarded at the database level, and an
`inventory.low_stock` event fired when an item crosses into low
territory.

Base version only — cost tracking, stock movements, audit trail and
auto-deduction arrive with the inventory core upgrade (#226), and
`treatment_consumables` (#225) links catalog treatments to these items.

## What it is

Clinic-scoped CRUD over the `InventoryItem` list plus one special
endpoint:

- `POST /{item_id}/adjust` applies a **relative** stock change
  (`+delta` restock / `-delta` consumption) as a single atomic SQL
  `UPDATE ... SET stock_quantity = stock_quantity + delta WHERE ...
  AND stock_quantity + delta >= 0 RETURNING *`.

Concurrency (the PR #153 post-mortem): quantity changes are guarded at
the DB level — a `CHECK (stock_quantity >= 0)` constraint backs every
path, and incremental changes never read-modify-write in app code.
Adjustments that would drive stock negative return `409`, and two
concurrent adjustments can neither go negative nor lose an increment.

## Low-stock model

Each item carries a `min_quantity` threshold. An item is low when
`stock_quantity <= min_quantity` (computed property on the model; also
filterable server-side via `?low_stock=true`). The
`inventory.low_stock` event fires once per not-low → low crossing:
on creation already at/below threshold, or on the first
update/adjustment that crosses it. No bundled subscriber — a future
notifications or procurement module subscribes without importing
inventory.

## Data model

- `inventory_items` — `id`, `clinic_id`, `name`, `category`
  (`consumables|equipment|office|other`, closed Literal set stored as
  `String(50)` so adding categories later is code-only),
  `unit`, `stock_quantity` numeric(12,2) with CHECK >= 0,
  `min_quantity` numeric(12,2), `notes` (nullable),
  `created_by` (nullable FK `users.id`), timestamps.

## Dependencies

`manifest.depends = []` — fully standalone. FKs point only at core
tables (clinics, users).

## Tenancy

Every query, mutation and agent tool filters by the caller's
`clinic_id`; cross-clinic access surfaces as 404.

## Lifecycle

`installable=True`, `auto_install=False` (activated from the module
admin UI), `removable=True`. Own Alembic branch (`inventory`) rooted on
core `"0001"`. Uninstall round-trip covered by
`test_uninstall_roundtrip.py`.

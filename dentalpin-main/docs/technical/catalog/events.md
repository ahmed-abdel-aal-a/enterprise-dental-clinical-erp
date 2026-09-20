---
module: catalog
last_verified_commit: 0000000
---

# Catalog — events

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

_This module does not publish any events._

## Subscribed

| Event | Handler | Effect |
|-------|---------|--------|
| `clinic.created` | `events.py:on_clinic_created` | Seed VAT types by country preset (`es` → exento/10/21, `generic` → exento only), categories and the default treatment catalog. Non-EUR clinics get every price at 0. Idempotent (skips existing rates / category keys / internal codes). Delegates to `seed.seed_clinic_defaults`, shared with `POST /catalog/seed` (manual repair path; failures here are logged, not raised). |

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method after `flush()` — the bus runs handlers
   inline, *before* the request commits. Pass `db=db` so transactional
   subscribers can join the transaction (ADR 0019, issue #183).
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.

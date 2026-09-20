---
module: media
last_verified_commit: 0000000
---

# Media — events

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

_This module does not publish any events._

## Subscribed

| Event | Handler | Mode | Effect |
|-------|---------|------|--------|
| `patient.archived` | `__init__.py::MediaModule._on_patient_archived` | transactional (ADR 0019) | Soft-archive the patient's documents, atomically with the archive itself. |

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method after `flush()` — the bus runs handlers
   inline, *before* the request commits. Pass `db=db` so transactional
   subscribers can join the transaction (ADR 0019, issue #183).
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.

---
module: verifactu
last_verified_commit: 0000000
---

# Verifactu — events

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

| Event | Where | Payload |
|-------|-------|---------|
| `verifactu.record.rejected` | `services/submission_queue.py` | `clinic_id`, `record_id`, `invoice_id`, AEAT error summary — emitted when AEAT rejects a record. |

## Subscribed

| Event | Handler | Mode | Effect |
|-------|---------|------|--------|
| `invoice.paid` | `events.on_invoice_paid` | own-session, payload-only (ADR 0019) | Queues the fiscal record for the paid invoice. |
| `verifactu.record.rejected` | `tasks.on_rejected_event` | own-session (spawns a task) | Emails the clinic admins, throttled to one alert per clinic per 30 min. |

Both are wired through `VerifactuModule.get_event_handlers()`, so they are
subscribed only while the module is installed (issue #91 / ADR 0020).

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method after `flush()` — the bus runs handlers
   inline, *before* the request commits. Pass `db=db` so transactional
   subscribers can join the transaction (ADR 0019, issue #183).
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.

---
module: recalls
last_verified_commit: 0000000
---

# Recalls — events

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

_This module does not publish any events._

## Subscribed

All four state-changing handlers are **transactional** (ADR 0019): a recall
mirrors an appointment, and `linked_appointment_id` is an FK to a row that
only exists in the publisher's transaction (issue #183).

| Event | Handler | Mode | Effect |
|-------|---------|------|--------|
| `appointment.scheduled` | `events.on_appointment_scheduled` | transactional | Auto-link the single matching pending recall (bails out when ambiguous). |
| `appointment.completed` | `events.on_appointment_completed` | transactional | Mark the linked recall done. |
| `appointment.cancelled` | `events.on_appointment_cancelled` | transactional | Unlink and send the recall back to `pending`. |
| `patient.archived` | `events.on_patient_archived` | transactional | Move active recalls to `needs_review`. |
| `treatment_plan.treatment_completed` | `events.on_treatment_plan_completed` | own-session (payload-only) | Logs only — suggestions are pulled by the frontend. |

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method after `flush()` — the bus runs handlers
   inline, *before* the request commits. Pass `db=db` so transactional
   subscribers can join the transaction (ADR 0019, issue #183).
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.

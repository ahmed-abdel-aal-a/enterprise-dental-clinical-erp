---
module: schedules
last_verified_commit: 0e9a0ac
---

# Schedules — events

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

This module does not publish any events. Occupancy data is exposed via
`GET /api/v1/schedules/analytics/*` endpoints, not events.

## Subscribed

| Event | Handler | Effect |
|-------|---------|--------|
| `appointment.scheduled` | `events.py:on_appointment_scheduled` | Recompute occupancy aggregates for the affected (professional, day). |
| `appointment.updated` | `events.py:on_appointment_updated` | Same — slot or duration may have moved. |
| `appointment.cancelled` | `events.py:on_appointment_cancelled` | Free the slot in the occupancy aggregates. |
| `clinic.created` | `events.py:on_clinic_created` | Seed a Mon–Fri weekly template (ES → 09–14 + 16–20; otherwise 09–18) instead of the 24/7 lazy default. No-op if a weekly schedule exists. |

The handlers must remain idempotent; agenda may re-publish on retry.

## Adding a new event

Schedules does not publish events today. If a future feature needs to
broadcast a state change:

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from the relevant service method, after the DB commit.
3. Add the row to the *Published* table above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.

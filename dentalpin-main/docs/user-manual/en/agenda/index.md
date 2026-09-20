---
module: agenda
last_verified_commit: b1b82f5
---

# Agenda

The agenda module manages the clinic's appointments: scheduling them,
moving them, assigning a room and professional, and walking them
through the workflow (scheduled → confirmed → in-room → completed →
billed). It is the operational hub for the front desk and the
clinical team during the day.

## Screens

- [Calendar and kanban](./screens/appointments.md) — weekly, daily,
  kanban, and mobile day views. Create, move, resize, and cancel
  appointments from the same screen.

## Quick reference

| Action | Required permission |
|--------|---------------------|
| View the calendar and open appointments | `agenda.appointments.read` |
| Create, move, resize, cancel | `agenda.appointments.write` |
| Advance an appointment status (transition) | `agenda.appointments.write` |
| View clinic rooms | `agenda.cabinets.read` |
| Create, rename, or delete rooms | `agenda.cabinets.write` |
| Edit the visit's clinical note | `clinical_notes.notes.write` |

Rooms are managed under **Settings → Workspace → Rooms** (host
module), not inside the agenda itself.

## Related modules

- **Patients** — every appointment belongs to a patient. The patient
  record links to the next appointment.
- **Schedules** — optional. When installed it computes real
  availability per professional and room; uninstalling it falls back
  to a default 08:00–21:00 window.
- **Recalls** — when an appointment is completed a follow-up modal
  appears and offers to schedule the patient's next recall.
- **Treatment plans** — from a plan you can jump into the agenda with
  the patient pre-selected to schedule the next session.
- **Notifications** — the agenda publishes `appointment.scheduled`,
  `appointment.status_changed`, and `appointment.cabinet_changed`
  events that sibling modules consume to notify patients.

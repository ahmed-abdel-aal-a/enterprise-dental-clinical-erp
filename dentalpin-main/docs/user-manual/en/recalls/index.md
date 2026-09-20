---
module: recalls
last_verified_commit: b1b82f5
---

# Recalls

The recalls module runs the **call-the-patient-back** workflow:
hygiene visits, checkups, orthodontic reviews, post-treatment
follow-ups, and so on. The front desk flags who to call in month
*X*, works a monthly call list, logs each attempt, and auto-links
the appointment the patient accepts.

Recalls **never sends messages** on its own — it only organizes the
queue and publishes `recall.*` events. A future outreach module
(WhatsApp, SMS, email) will subscribe to those events.

## Screens

- [Call list](./screens/recalls.md) — monthly list with filters,
  counters, and per-row quick actions.

## Quick reference

| Action | Required permission |
|--------|---------------------|
| View the list, counters, export CSV | `recalls.read` |
| Create, snooze, complete, link an appointment | `recalls.write` |
| Delete a recall | `recalls.delete` (admin) |
| Edit settings (intervals, category map) | `recalls.write` |

## Related modules

- **Patients** — recalls are always tied to a patient. Archiving the
  patient or flagging `do_not_contact` moves their active recalls to
  the **Needs review** bucket (they are not deleted).
- **Agenda** — when a new appointment is scheduled for a patient who
  has a single pending recall, the recall is auto-linked. Completing
  the appointment marks the recall as *done*.
- **Treatment plans** — the `treatment_plan.treatment_completed`
  event drives a recall suggestion tied to the treatment (visible in
  *Next suggestions* on the list).
- **Odontogram** — a *Schedule recall* button on each treatment.
- **Notifications / outreach (future)** — will consume the
  `recall.created`, `recall.snoozed`, `recall.completed`,
  `recall.cancelled` events to automate outreach.

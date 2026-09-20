---
module: treatment_plan
last_verified_commit: b1b82f5
---

# Treatment plans

The treatment plans module is the **hub** that ties the patient to
their planned treatments, the budget that backs them, and the
odontogram they are performed on. It runs the full clinical-meets-
commercial workflow: draft → pending → active → completed, with
branches to *closed* (rejected, expired, cancelled, abandoned).

A plan groups everything you intend to do for the patient, keeps it
in sync with a budget, marks executions when a treatment is performed
on the odontogram or an appointment is completed, and publishes
events for recalls, timeline, and other modules.

## Screens

- [Plans inbox](./screens/treatment-plans.md) — five-tab inbox
  (Drafts / Pending / Active / Completed / Closed) plus the
  follow-up pipeline.
- [Plan detail](./screens/treatment-plans_id.md) — edit items, move
  through states, mark treatments as done, see the linked budget,
  and record contacts.
- [New plan](./screens/treatment-plans_new.md) — create a plan for
  a patient.

## Quick reference

| Action | Required permission |
|--------|---------------------|
| View inbox, detail, and pipeline | `treatment_plan.plans.read` |
| Create/edit plans, add or reorder items, log contacts | `treatment_plan.plans.write` |
| Confirm a plan (draft → pending) | `treatment_plan.plans.confirm` |
| Close a plan | `treatment_plan.plans.close` |
| Reactivate a closed plan | `treatment_plan.plans.reactivate` |

## Related modules

- **Patients / Odontogram / Catalog** — sources for the plan: the
  catalog defines possible treatments, the odontogram says where
  they go.
- **Budget** — confirming a plan creates/keeps in sync a linked
  budget via snapshot events (`treatment_plan.treatment_added /
  _removed / budget_sync_requested`). Accepting the budget on the
  budget module moves the plan to *active*.
- **Agenda** — completing an appointment marks linked planned items
  as performed.
- **Recalls** — completing a treatment (with
  `treatment_category_key`) drives a recall suggestion.
- **Media** — clinical attachments for the plan (x-rays, photos)
  live in `media`.
- **Clinical notes** — execution-time notes live in their own module
  since issue #60. Plans no longer store `note_body` themselves.

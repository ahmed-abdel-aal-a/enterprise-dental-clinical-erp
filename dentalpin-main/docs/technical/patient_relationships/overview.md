---
module: patient_relationships
last_verified_commit: 0000000
---

# patient_relationships — overview

Patient-to-patient relationships ("Lien de Parentée") — parent/child,
spouse, sibling, guardian/ward, or other — surfaced inline on the
patient page.

## What it is

Two endpoints under `/patients/{patient_id}/relationships`: list, and
create/update/delete. The inverse label (parent<->child, spouse<->spouse,
sibling<->sibling, guardian<->ward, other<->other) is derived at read
time, not stored, so the two sides of a relationship can never drift
out of sync.

## Data model

`patient_relationships` — a directed link between two patients
within the same clinic (`patient_id`, `related_patient_id`,
`relationship_type`, both FK to `patients.id`).

Originally also carried insurance exemption status (APCI/ALD); dropped
in `prel_0002` — exemption is now a computed flag off systemic-disease
reference data, not a manually entered field.

## Tenancy

Every lookup filters by `clinic_id`. Update/delete additionally require
the URL's `patient_id` (already verified to belong to the caller's
clinic) to match the relationship row's `patient_id` or
`related_patient_id` — enforced at both the query level and the router
level, not just one or the other.

## Constraints

`prel_0001`'s migration FKs to `patients.id`, which lives on the
unlabeled/core chain rather than a branch of its own — `depends_on =
("pat_0003",)` makes that ordering explicit rather than relying on
Alembic's default multi-head resolution (see CHANGELOG.md).

# patient_relationships module

Patient-to-patient relationships ("Lien de Parentée") — parent/child,
spouse, sibling, guardian/ward, or other, surfaced inline on the
patient page. Originally also carried insurance exemption status
(APCI/ALD); that was dropped in `prel_0002` — exemption is now a
computed flag off systemic-disease reference data, not a manually
entered field, so it doesn't belong here.

## What it does

Two endpoints under `/patients/{patient_id}/relationships`: list (with
the inverse label derived at read time so the two sides of a
relationship can never drift out of sync — see `service.py`'s
`INVERSE_RELATIONSHIP_TYPE`), and create/update/delete, gated behind
`patient_relationships.read`/`.write`.

## Tenancy

`PatientRelationship` has its own `clinic_id` column and every lookup
(`list_relationships`, `get_relationship`) filters on it. Update/delete
additionally require the URL's `patient_id` (already verified to
belong to the caller's clinic via `_ensure_patient`) to match the
relationship row's `patient_id` or `related_patient_id` — this is
enforced at both the query level and the router level, not just one or
the other, so a future caller that reaches `get_relationship` directly
doesn't inherit an unscoped lookup by accident.

## Dependencies

`manifest.depends = ["patients"]` — reads `Patient.full_name` for the
"other side" of each relationship in responses, and both tables in
`prel_0001`'s migration FK to `patients.id`. `prel_0001` declares
`depends_on = ("pat_0003",)` for that reason: `patients` has no branch
label of its own (it lives on the same unlabeled/core chain as "0001"),
so without an explicit `depends_on`, a fresh install can't guarantee
`patients`' migrations have run before this module's FK needs them to
have.

## Lifecycle

- `installable=True`, `auto_install=False` (repo policy for optional
  modules: the admin activates it from the module admin UI),
  `removable=True`.
- Own Alembic branch (`patient_relationships`), rooted independently on core
  `"0001"` per ADR 0002 — `prel_0001` (initial schema) then `prel_0002`
  (drops the exemption-status table).
- No standalone nav entry — surfaces via the `patient.summary.cards`
  slot (`slots.client.ts`), same extension point `patients_clinical`
  uses.

## CHANGELOG

See `./CHANGELOG.md`.

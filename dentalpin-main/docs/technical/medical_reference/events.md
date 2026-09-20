---
module: medical_reference
last_verified_commit: 829bdd25
---

# medical_reference — events

This module publishes and consumes **no events**.

Rationale: reference-list CRUD is user-initiated state that no other
module needs to react to asynchronously, and the per-patient flags are
computed on read (`GET /patients/{patient_id}/flags`), not maintained
by event handlers — there is no denormalized flag state to keep in
sync, so there is nothing to transact (ADR 0019 does not apply).

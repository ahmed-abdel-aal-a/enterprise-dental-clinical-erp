---
module: medical_reference
last_verified_commit: 829bdd25
---

# medical_reference — permissions

Namespaced by the registry from the module's `get_permissions()`.

| Permission | Gates | Endpoints |
|------------|-------|-----------|
| `medical_reference.read` | Search/list any reference list; list interactions & contraindications; read a patient's active flags | `GET /api/v1/medical_reference/allergies\|medications\|diseases\|surgeries`, `GET …/interactions`, `GET …/contraindications`, `GET /api/v1/medical_reference/patients/{patient_id}/flags` |
| `medical_reference.write` | Create/update/deactivate reference items, interactions and contraindications | `POST`/`PUT`/`DELETE` on the same six resource paths |

Default role mapping:

| Role | Permissions |
|------|-------------|
| `admin` | all (`*`) |
| `dentist` | read, write |
| `hygienist` | read only |
| `assistant` | read only |
| `receptionist` | read only |

Dentists get `write` deliberately: recording a new allergy/medication on
the fly while taking a medical history is a clinical judgment call,
matching `patients_clinical`'s own `medical.read`/`medical.write` split
for the same category of data.

Frontend slot registrations (searchable name fields, header warning
chips) are gated on `medical_reference.read` — without it the medical
history form falls back to plain free-text inputs.

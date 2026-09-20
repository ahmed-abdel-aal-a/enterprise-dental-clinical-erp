---
module: patient_relationships
last_verified_commit: 0000000
---

# patient_relationships — permissions

Namespaced by the registry from the module's `get_permissions()`.

| Permission | Gates | Endpoints |
|------------|-------|-----------|
| `patient_relationships.read` | View a patient's relationships | `GET /api/v1/patient_relationships/patients/{patient_id}/relationships` |
| `patient_relationships.write` | Create, update, delete a relationship | `POST /api/v1/patient_relationships/patients/{patient_id}/relationships`, `PUT …/relationships/{id}`, `DELETE …/relationships/{id}` |

Default role mapping:

| Role | Permissions |
|------|-------------|
| `admin` | all (`*`) |
| `dentist` | read, write |
| `hygienist` | read only |
| `assistant` | read, write |
| `receptionist` | read, write |

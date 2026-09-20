---
module: contacts
last_verified_commit: 0a0651a
---

# contacts — permissions

Namespaced by the registry from the module's `get_permissions()`.

| Permission | Gates | Endpoints |
|------------|-------|-----------|
| `contacts.read` | View the directory | `GET /api/v1/contacts/`, `GET /api/v1/contacts/{id}` |
| `contacts.write` | Create, edit, soft-delete a contact | `POST /api/v1/contacts/`, `PATCH /api/v1/contacts/{id}`, `DELETE /api/v1/contacts/{id}` |

Default role mapping:

| Role | Permissions |
|------|-------------|
| `admin` | all (`*`) |
| `dentist` | read only |
| `hygienist` | read only |
| `assistant` | read, write |
| `receptionist` | read, write |

Front-desk staff (assistant/receptionist) manage the directory
day-to-day; clinicians only consult it.

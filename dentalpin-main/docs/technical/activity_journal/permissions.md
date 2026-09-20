---
module: activity_journal
---

# activity_journal — permissions

Namespaced by the registry from the module's `get_permissions()`.

| Permission | Gates | Endpoints / tools |
|------------|-------|-------------------|
| `activity_journal.read` | List, view, payload detail | `GET /api/v1/activity_journal`, `GET /api/v1/activity_journal/{id}`, agent tool `search_activity` |

There is **no write permission**: rows are appended exclusively by the
transactional event handlers inside publishers' transactions. No
endpoint, tool or service can create, edit or delete a journal entry.

Default role mapping: **admin only** — the log records which staff
member did what, so it is sensitive by nature
(`role_permissions = {"admin": ["*"]}`). Clinics can grant
`activity_journal.read` to other roles from the module admin UI.

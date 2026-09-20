---
module: contacts
last_verified_commit: 0a0651a
---

# contacts — overview

Directory of external labs, suppliers, delegates, and other providers
the clinic deals with. Standalone (`manifest.depends = []`); intended
as the foundation for a future `lab_orders` module, where a work order
links to a contact created here.

## What it is

One entity (`Contact`) with plain CRUD under `/api/v1/contacts/*`:
list (type filter + name/notes search + pagination), get, create (201),
patch, and soft-delete (204). One Nuxt page (`/contacts`) with a table,
search box, type filter, and a create/edit modal.

## Data model

`contacts` — `id`, `clinic_id` (FK `clinics.id`, indexed), `name`,
`contact_type` (`lab` | `supplier` | `delegate` | `other`, indexed),
`phone`, `email`, `address`, `notes`, `is_active`, timestamps.

Deletion is soft (`is_active=false`): once lab-order history exists, an
old order must still be able to show which lab it went to. The default
listing filters to active rows; `include_inactive=true` returns
everything, and `GET /contacts/{id}` always resolves.

## Tenancy

Every `ContactService` query filters by `clinic_id`; get/update/delete
resolve through the same clinic-scoped lookup (404 on cross-tenant ids).
Covered by `tests/modules/contacts/test_contacts.py`.

## Lifecycle

`installable=True`, `auto_install=False` (activated manually from
Settings → Modules), `removable=True`. Migrations live on the
`contacts` Alembic branch (`con_0001`), chained off core `0001`; no
cross-module FKs, so uninstall downgrades cleanly.

## Agent tools

`list_contacts` (READ) and `create_contact` (WRITE), thin wrappers over
`ContactService`, clinic-scoped via `ctx.clinic_id`. See the module's
`CLAUDE.md` for the table.

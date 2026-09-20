---
module: contacts
last_verified_commit: 0a0651a
---

# Contacts

The contacts module is the clinic's directory of **external providers**:
dental labs, material suppliers, brand delegates, and anyone else the
clinic works with who is not a patient or a staff member.

It is an optional module — an administrator activates it from
**Settings → Modules**. Once active, **Contacts** appears in the
sidebar for every user with permission to view it.

## Screens

- [Contact directory](./screens/list.md) — searchable list with a type
  filter and a create/edit form.

## Quick reference

| Action | Required permission |
|--------|---------------------|
| View the directory | `contacts.read` |
| Add, edit, or deactivate a contact | `contacts.write` |

By default dentists and hygienists can only consult the directory;
assistants and receptionists can also manage it.

## Good to know

- **Deleting is deactivating.** A deleted contact disappears from the
  list but is kept in the database, so historical records that point to
  it (e.g. future lab orders) stay intact.
- Contact types: **Lab**, **Supplier**, **Delegate**, **Other**.

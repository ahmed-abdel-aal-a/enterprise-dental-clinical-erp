---
module: lab_orders
last_verified_commit: c9c20493
---

# lab_orders — overview

`lab_orders` records work sent to an external dental laboratory for a patient and tracks it through `sent`, `in_progress`, `ready`, `received`, or `cancelled`.

## Data model

`lab_orders` stores the clinic, patient, laboratory contact, work type, optional prosthodontic details, status, dates, notes, and creator.

## Dependencies

`manifest.depends = ["patients", "contacts"]`. Both cross-module foreign keys are declared in the migration graph as `depends_on` entries for the corresponding migration tips.

## Tenancy

Every read, create/update validation, enrichment query, and agent tool is scoped by the caller's `clinic_id`. Orders are never hard-deleted — cancellation is a status change.

## Frontend

The module provides two pages:

- `/lab-orders/new` — form for creating a lab work order.
- `/lab-orders` — status-tracking list with inline status changes.

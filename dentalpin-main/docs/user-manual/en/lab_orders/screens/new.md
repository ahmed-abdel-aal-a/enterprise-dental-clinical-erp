---
module: lab_orders
screen: new
route: /lab-orders/new
related_endpoints:
  - POST /api/v1/lab_orders/
  - GET /api/v1/contacts/
related_permissions:
  - lab_orders.write
related_paths:
  - backend/app/modules/lab_orders/router.py
  - backend/app/modules/lab_orders/frontend/pages/lab-orders/new.vue
last_verified_commit: c9c20493
---

# New lab order

Form to send work to an external laboratory for a patient.

## Fields

- **Patient** (required) — the patient the work is for.
- **Laboratory** (required) — a contact of type `lab`; create one in
  Contacts first if the list is empty.
- **Work type** (required) — crown, bridge, denture, implant, veneer,
  orthodontic, repair or other.
- **Tooth / reference**, **impression type**, **antagonist
  information** and **Vita Classical shade** — optional prosthodontic
  details that help the laboratory reproduce the case.
- **Sent date** (required) and **expected return date**.
- **Notes** — free-text instructions for the laboratory.

## Behaviour

Submitting posts to `/api/v1/lab_orders/` and redirects back to the
orders list, where the new order appears with status `Sent`. The form
requires `lab_orders.write`; users without it never reach this page from
the navigation.

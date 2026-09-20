---
module: lab_orders
screen: index
route: /lab-orders
related_endpoints:
  - GET /api/v1/lab_orders/
  - GET /api/v1/lab_orders/{order_id}
  - PATCH /api/v1/lab_orders/{order_id}
related_permissions:
  - lab_orders.read
  - lab_orders.write
related_paths:
  - backend/app/modules/lab_orders/router.py
  - backend/app/modules/lab_orders/frontend/pages/lab-orders/index.vue
last_verified_commit: e0af282a
---

# Lab work orders

Use **Lab orders** to send work to an external laboratory and track its status.

## Create a lab order

Open **New lab order**, select the patient and laboratory contact, enter the work type, optional tooth/impression/shade details, dates, and notes, then choose **Send order**.

## Track status

Open **Lab orders** to review existing orders. Use the status selector to move an order through `Sent`, `In progress`, `Ready`, `Received`, or `Cancelled`. Roles without write access see the status as a read-only label.

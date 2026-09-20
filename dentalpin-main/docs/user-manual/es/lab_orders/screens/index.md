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

# Trabajos de laboratorio

Use **Trabajos de laboratorio** para enviar trabajos a un laboratorio externo y seguir su estado.

## Crear un trabajo

Abra **Nuevo trabajo de laboratorio**, seleccione el paciente y el contacto del laboratorio, complete el tipo de trabajo, los datos dentales opcionales, las fechas y las notas, y pulse **Enviar trabajo**.

## Seguir el estado

Abra **Trabajos de laboratorio** para revisar los pedidos existentes. Use el selector de estado para avanzar por `Enviado`, `En curso`, `Listo`, `Recibido` o `Cancelado`. Los roles sin permiso de escritura ven el estado como una etiqueta de solo lectura.

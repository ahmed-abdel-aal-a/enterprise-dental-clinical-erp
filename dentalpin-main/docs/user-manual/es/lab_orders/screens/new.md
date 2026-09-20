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

# Nuevo trabajo de laboratorio

Formulario para enviar trabajo a un laboratorio externo para un paciente.

## Campos

- **Paciente** (obligatorio): el paciente para el que es el trabajo.
- **Laboratorio** (obligatorio): un contacto de tipo `lab`; créalo en
  Contactos primero si la lista está vacía.
- **Tipo de trabajo** (obligatorio): corona, puente, prótesis, implante,
  carilla, ortodoncia, reparación u otro.
- **Diente / referencia**, **tipo de impresión**, **información del
  antagonista** y **color Vita Classical**: detalles protésicos
  opcionales que ayudan al laboratorio a reproducir el caso.
- **Fecha de envío** (obligatoria) y **fecha de retorno esperada**.
- **Notas**: instrucciones libres para el laboratorio.

## Comportamiento

Al enviar se hace un POST a `/api/v1/lab_orders/` y se vuelve a la lista
de trabajos, donde el nuevo aparece con estado `Enviado`. El formulario
requiere `lab_orders.write`; los usuarios sin ese permiso no llegan a
esta página desde la navegación.

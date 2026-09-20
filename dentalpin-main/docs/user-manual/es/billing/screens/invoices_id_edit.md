---
module: billing
screen: edit
route: /invoices/[id]/edit
related_endpoints:
  - DELETE /api/v1/billing/invoices/{invoice_id}/items/{item_id}
  - GET /api/v1/billing/invoices/{invoice_id}
  - GET /api/v1/billing/series
  - GET /api/v1/billing/settings
  - PATCH /api/v1/billing/invoices/{invoice_id}/billing-party
  - POST /api/v1/billing/invoices/{invoice_id}/items
  - PUT /api/v1/billing/invoices/{invoice_id}
  - PUT /api/v1/billing/invoices/{invoice_id}/items/{item_id}
related_permissions:
  - billing.read
  - billing.write
related_paths:
  - backend/app/modules/billing/frontend/pages/invoices/[id]/edit.vue
  - backend/app/modules/billing/router.py
last_verified_commit: b1b82f5
---

# Editar borrador de factura

Formulario para editar un borrador de factura. **Solo disponible
cuando la factura está en estado `draft`.** Las facturas emitidas no
se editan: hay que anular y volver a emitir, o emitir un abono.

## De un vistazo

- **Estado válido:** `draft`. Cualquier otro estado redirige al
  [detalle](./invoices_id.md) y muestra los datos en solo lectura.
- **Receptor (pagador).** Por defecto el paciente. Si pulsas
  *Pagador distinto* (PATCH `billing-party`) puedes apuntar a un
  tercero (compañía, mutua, familiar) — la factura se emite a
  nombre del pagador alternativo.
- **Líneas.** Añadir, editar, borrar líneas. Cada línea referencia
  un ítem del catálogo con descripción, cantidad, precio
  unitario, descuento e IVA (snapshot del catálogo al crear la
  factura).
- **Serie de facturación.** No se elige aquí: la serie activa
  asigna número al emitir. Si necesitas otra serie, cambia la
  serie activa desde *Ajustes → Series de facturación*.

## Editar una factura

> Requiere `billing.write`.

1. Cambia descuento, cantidad, IVA o añade líneas.
2. Si el pagador no es el paciente, pulsa *Pagador distinto* y
   rellena los datos legales del tercero.
3. **Guardar**. La factura sigue en `draft`. Para emitirla, vuelve
   al [detalle](./invoices_id.md) y pulsa **Emitir**.

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Cargar el formulario | `billing.read` |
| Editar líneas y datos del receptor | `billing.write` |

## Resolución de problemas

- **Esta pantalla redirige al detalle.** La factura no está en
  `draft`. Solo se editan borradores.
- **No me deja añadir un ítem.** Comprueba que el ítem está activo
  en el catálogo de la clínica y que tienes `catalog.read`.
- **El total no actualiza al cambiar IVA.** Guarda para que el
  servidor recalcule; el frontend muestra el resultado en directo,
  pero la fuente de verdad es la respuesta del backend.

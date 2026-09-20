---
module: budget
last_verified_commit: b1b82f5
---

# Presupuestos (budget)

El módulo de presupuestos gestiona los presupuestos dentales del
paciente: ítems del catálogo, descuentos, IVA, versiones, firma, PDF
y un flujo claro `borrador → enviado → aceptado → completado` (con
ramas a *rechazado*, *expirado* o *cancelado*).

Es el puente entre el plan de tratamiento del clínico y la
facturación: cuando el paciente acepta un presupuesto se puede emitir
la factura desde el módulo `billing` y cobrarlo desde `payments`.

## Pantallas

- [Listado de presupuestos](./screens/budgets.md) — buscar, filtrar
  por estado / pago / validez, ordenar y abrir presupuestos.
- [Detalle del presupuesto](./screens/budgets_id.md) — editar
  líneas, totales, enviar, aceptar/rechazar, renegociar, ver firma
  y descargar el PDF.
- [Nuevo presupuesto](./screens/budgets_new.md) — crear un
  presupuesto desde cero o desde un plan de tratamiento.
- [Aceptación pública del paciente](./screens/p_budget_token.md) —
  vista pública para el paciente (sin sesión de la app) con
  verificación 2FA, aceptación o rechazo desde su móvil.

## Referencia rápida

| Acción | Permiso requerido |
|--------|-------------------|
| Ver presupuestos y descargar PDF | `budget.read` |
| Crear, editar, enviar, aceptar (en clínica solo con permiso explícito) | `budget.write` |
| Borrar presupuesto | `budget.admin` |
| Renegociar (crear nueva versión sin perder historial) | `budget.renegotiate` |
| Aceptar un presupuesto firmando en clínica (tablet) | `budget.accept_in_clinic` |

## Módulos relacionados

- **Pacientes / Catálogo / Odontograma** — dependencias directas.
  Los ítems del presupuesto referencian al catálogo y, opcionalmente,
  a piezas y superficies del odontograma.
- **Planes de tratamiento** — un plan puede generar presupuestos y
  sincronizarse cuando se añaden o quitan tratamientos. La
  comunicación es por eventos (snapshot), nunca por imports.
- **Facturación (`billing`)** — desde un presupuesto aceptado puedes
  saltar a *Crear factura desde este presupuesto*.
- **Cobros (`payments`)** — la barra lateral del detalle muestra
  cobrado / pendiente y el botón *Cobrar* (lo aporta el módulo de
  cobros).
- **Notificaciones** — se publican eventos `budget.sent`,
  `budget.accepted`, `budget.rejected`, `budget.expired`,
  `budget.viewed`, `budget.reminder_sent` para outreach futuro.

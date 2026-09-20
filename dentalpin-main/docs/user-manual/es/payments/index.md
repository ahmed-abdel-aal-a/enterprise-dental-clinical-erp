---
module: payments
last_verified_commit: b1b82f5
---

# Cobros (payments)

El módulo de cobros lleva la **caja real** de la clínica: cada pago
que recibes del paciente, repartido entre presupuestos y *a cuenta*,
con sus reembolsos asociados y un libro mayor por paciente. También
alimenta los informes financieros del módulo `reports`.

Es un módulo **centrado en el paciente**, no en la factura. Eso
significa que un pago puede cubrir varios presupuestos a la vez,
quedar parcialmente *a cuenta* o repartirse entre tratamientos
distintos. La facturación enlaza los pagos cuando hace falta emitir
una factura formal — nunca al revés.

## Pantallas

- [Listado de cobros](./screens/payments.md) — todos los cobros con
  filtros, asignaciones y atajo de reembolso.
- [Informes de cobros](./screens/reports_payments.md) — KPIs,
  tendencia, métodos de pago, profesionales, *aging* y reembolsos.

## Referencia rápida

| Acción | Permiso requerido |
|--------|-------------------|
| Ver listado, libro mayor del paciente y asignaciones | `payments.record.read` |
| Registrar un cobro o reasignarlo | `payments.record.write` |
| Emitir un reembolso | `payments.record.refund` (admin/dentista por defecto) |
| Ver los informes de cobros | `payments.reports.read` |

## Módulos relacionados

- **Presupuestos (`budget`)** — todo pago puede asignarse a uno o
  varios presupuestos del paciente. El presupuesto muestra una
  tarjeta lateral *Cobrado / Pendiente* con el desglose.
- **Pacientes** — la pestaña *Administración* de la ficha incluye el
  libro mayor del paciente (KPIs + timeline + acción de reembolso).
- **Facturación** — depende de cobros, no al revés. Una factura puede
  enlazar uno o varios cobros (`invoice_payments` lo gestiona en el
  módulo `billing`).
- **Odontograma y planes de tratamiento** — alimentan a cobros con
  el dato de *lo ganado* (`PatientEarnedEntry`) vía eventos
  `odontogram.treatment.performed` y
  `treatment_plan.treatment_completed`. Los informes lo usan para el
  *aging*.
- **Informes (`reports`)** — la página `/reports` enlaza a
  `/reports/payments` cuando el módulo de cobros está instalado.

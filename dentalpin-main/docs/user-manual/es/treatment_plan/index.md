---
module: treatment_plan
last_verified_commit: b1b82f5
---

# Planes de tratamiento

El módulo de planes de tratamiento es el **hub** que une al paciente
con sus tratamientos planificados, el presupuesto que los respalda
y el odontograma sobre el que se ejecutan. Recorre todo el flujo
clínico-comercial: borrador → pendiente → activo → completado, con
ramas a *cerrado* (rechazado, expirado, cancelado, abandonado).

Un plan agrupa todo lo que se va a hacerle al paciente, lo sincroniza
con un presupuesto, marca ejecuciones cuando se hace un tratamiento
sobre el odontograma o se completa una cita, y publica eventos para
recalls, timeline y otros módulos.

## Pantallas

- [Bandeja de planes](./screens/treatment-plans.md) — bandeja con
  cinco pestañas (Borradores / Pendientes / Activos / Completados /
  Cerrados) y la cola de seguimiento.
- [Detalle del plan](./screens/treatment-plans_id.md) — editar
  ítems, mover de estado, marcar tratamientos como hechos, ver el
  presupuesto enlazado y registrar contactos.
- [Nuevo plan](./screens/treatment-plans_new.md) — crear un plan
  para un paciente.

## Referencia rápida

| Acción | Permiso requerido |
|--------|-------------------|
| Ver bandeja, detalles y pipeline | `treatment_plan.plans.read` |
| Crear/editar planes, añadir o reordenar ítems, registrar contactos | `treatment_plan.plans.write` |
| Confirmar un plan (borrador → pendiente) | `treatment_plan.plans.confirm` |
| Cerrar un plan | `treatment_plan.plans.close` |
| Reactivar un plan cerrado | `treatment_plan.plans.reactivate` |

## Módulos relacionados

- **Pacientes / Odontograma / Catálogo** — fuentes del plan: el
  catálogo define los tratamientos posibles, el odontograma indica
  dónde van.
- **Presupuestos (`budget`)** — al confirmar un plan se crea/sincroniza
  un presupuesto enlazado vía eventos snapshot
  (`treatment_plan.treatment_added` / `treatment_removed` /
  `budget_sync_requested`). Aceptar el presupuesto en el módulo de
  presupuestos pasa el plan a *activo*.
- **Agenda** — al completar una cita marcamos los ítems planificados
  de esa cita como hechos.
- **Recalls** — al completar un tratamiento (con
  `treatment_category_key`) se sugiere un recall asociado.
- **Multimedia** — adjuntos clínicos del plan (radiografías, fotos)
  viven en `media`.
- **Notas clínicas (`clinical_notes`)** — las notas asociadas a la
  ejecución viven en su módulo desde el issue #60. El plan ya no
  guarda `note_body` propio.

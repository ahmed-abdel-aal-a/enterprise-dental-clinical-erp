---
module: treatment_plan
screen: create
route: /treatment-plans/new
related_endpoints:
  - GET /api/v1/treatment_plan/treatment-plans
  - GET /api/v1/treatment_plan/treatment-plans/patient/{patient_id}
  - POST /api/v1/treatment_plan/treatment-plans
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/items
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/generate-budget
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/link-budget
related_permissions:
  - treatment_plan.plans.read
  - treatment_plan.plans.write
related_paths:
  - backend/app/modules/treatment_plan/frontend/pages/treatment-plans/new.vue
  - backend/app/modules/treatment_plan/router.py
last_verified_commit: b1b82f5
---

# Nuevo plan de tratamiento

Formulario para crear un plan de tratamiento para un paciente. Al
guardar, el plan nace en estado `draft` y se abre el
[detalle](./treatment-plans_id.md) para añadir ítems, confirmar y
generar presupuesto.

## De un vistazo

- **Origen.** Suele llegarse desde la ficha del paciente (paciente
  preseleccionado) o desde la bandeja con **Nuevo plan**.
- **Profesional asignado.** Recepción puede asignar al profesional;
  un profesional sin permiso de admin solo puede asignarse a sí
  mismo.
- **Ítems iniciales.** El formulario permite añadir tratamientos
  ahora o crear el plan vacío y añadirlos desde el detalle.
- **Presupuesto.** No se crea aquí. Tras crear el plan, en el
  detalle pulsas **Generar presupuesto** o **Enlazar con presupuesto
  existente**.

## Crear un plan

> Requiere `treatment_plan.plans.write`.

1. Selecciona paciente (si no viene preseleccionado).
2. Asigna profesional. Añade un título descriptivo (opcional pero
   recomendable cuando un paciente tiene varios planes).
3. Añade tratamientos del catálogo o, si el paciente tiene
   tratamientos planificados en el odontograma, marcalos para que
   queden enlazados a ítems del plan.
4. **Guardar**. Se publica `treatment_plan.created` y entras al
   detalle.

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Acceder al formulario y ver el catálogo | `treatment_plan.plans.read` |
| Crear el plan | `treatment_plan.plans.write` |

## Resolución de problemas

- **Selector de profesional vacío.** Cuando solo puedes asignarte a
  ti, el selector queda fijado a tu usuario. Si tu rol es admin/
  recepción y no salen profesionales, créalos o actívalos en
  *Ajustes → Usuarios*.
- **No me deja añadir un tratamiento del odontograma.** El paciente
  no tiene tratamientos planificados visibles. Crea uno desde la
  pestaña Clínica del paciente antes de planificarlo.

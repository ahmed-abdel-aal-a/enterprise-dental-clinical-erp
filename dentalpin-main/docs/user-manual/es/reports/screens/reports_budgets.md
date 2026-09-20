---
module: reports
screen: budgets
route: /reports/budgets
related_endpoints:
  - GET /api/v1/reports/budgets/by-professional
  - GET /api/v1/reports/budgets/by-status
  - GET /api/v1/reports/budgets/by-treatment
  - GET /api/v1/reports/budgets/summary
related_permissions:
  - reports.budgets.read
related_paths:
  - backend/app/modules/reports/frontend/pages/reports/budgets.vue
  - backend/app/modules/reports/router.py
last_verified_commit: b1b82f5
---

# Informes de presupuestos

Cuadro de mando de presupuestos. Mide la **conversión** desde
borrador a aceptado, el tiempo medio en cada estado y los motivos
de cierre. Es la herramienta de gerencia para detectar cuellos de
botella en la captación y para entender qué tratamientos se aceptan
mejor.

## De un vistazo

- **Resumen** — totales por estado en el rango (`draft`, `sent`,
  `accepted`, `rejected`, `expired`, `cancelled`), totales
  monetarios y tasa de conversión global (`accepted / sent`).
- **Por estado** — distribución de presupuestos por estado, sobre el
  rango elegido.
- **Por profesional** — tasa de conversión y volumen monetario por
  profesional asignado. Útil para benchmarking interno y formación.
- **Por tratamiento** — qué ítems del catálogo aparecen con más
  frecuencia y cuáles tienen peor conversión.

## Drill-downs

- Cada barra o fila lleva al listado de presupuestos
  ([/budgets](../../budget/screens/budgets.md)) filtrado por estado,
  profesional o motivo de cierre.
- Para auditar un presupuesto concreto desde aquí, abre el
  *drill-down* y entra al detalle.

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Ver el cuadro y los desgloses | `reports.budgets.read` |
| Abrir el listado de presupuestos (drill-down) | `budget.read` |

## Resolución de problemas

- **Conversión 0%.** En el rango aún no hay presupuestos en
  `accepted`. Amplía el rango o revisa el pipeline de aceptaciones.
- **Por profesional no aparece nadie.** El presupuesto no tiene
  `assigned_professional_id` informado. Es opcional; asigna
  profesional al crear/editar el presupuesto para verlos aquí.
- **Una tarjeta abre el listado vacío.** El filtro del drill-down
  combina rango + estado/profesional, y la combinación quizá no
  tiene presupuestos. Quita un filtro.

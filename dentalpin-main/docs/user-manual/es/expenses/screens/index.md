---
module: expenses
screen: index
route: /expenses
related_endpoints:
  - GET /api/v1/expenses
  - GET /api/v1/expenses/monthly-totals
  - POST /api/v1/expenses
  - DELETE /api/v1/expenses/{expense_id}
related_permissions:
  - expenses.read
  - expenses.write
related_paths:
  - backend/app/modules/expenses/frontend/pages/expenses/index.vue
last_verified_commit: 3d0fc1d1
---

# Lista de gastos

Seguimiento de gastos fijos y recurrentes de la clínica — alquiler,
suministros, salarios, material, equipamiento, seguro, mantenimiento y
otros.

## Permisos

- El módulo es **solo para admin de fábrica**; la clínica puede conceder
  `expenses.read` / `expenses.write` a otros roles desde la UI de
  administración de módulos.
- `expenses.read` — ver la lista y los totales mensuales.
- `expenses.write` — añadir y eliminar gastos.

## Qué hace esta pantalla

- **Filtrar** la lista por categoría.
- **Añadir gasto** — abre un modal para categoría, importe, fecha y una
  descripción opcional.
- **Totales mensuales** — una insignia por categoría para el mes actual.
- **Eliminar** por fila (requiere `expenses.write`) con diálogo de
  confirmación.
- **Paginación** — en servidor, 20 filas por página.


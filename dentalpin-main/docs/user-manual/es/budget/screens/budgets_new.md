---
module: budget
screen: create
route: /budgets/new
related_endpoints:
  - DELETE /api/v1/budget/budgets/{budget_id}
  - DELETE /api/v1/budget/budgets/{budget_id}/items/{item_id}
  - GET /api/v1/budget/budgets
  - GET /api/v1/budget/budgets/{budget_id}
  - GET /api/v1/budget/budgets/{budget_id}/history
  - GET /api/v1/budget/budgets/{budget_id}/pdf
  - GET /api/v1/budget/budgets/{budget_id}/pdf/preview
  - GET /api/v1/budget/budgets/{budget_id}/pdf/signed
  - GET /api/v1/budget/budgets/{budget_id}/signature
  - GET /api/v1/budget/budgets/{budget_id}/versions
  - POST /api/v1/budget/budgets
  - POST /api/v1/budget/budgets/{budget_id}/accept
  - POST /api/v1/budget/budgets/{budget_id}/accept-in-clinic
  - POST /api/v1/budget/budgets/{budget_id}/cancel
  - POST /api/v1/budget/budgets/{budget_id}/duplicate
  - POST /api/v1/budget/budgets/{budget_id}/items
  - POST /api/v1/budget/budgets/{budget_id}/reject
  - POST /api/v1/budget/budgets/{budget_id}/renegotiate
  - POST /api/v1/budget/budgets/{budget_id}/resend
  - POST /api/v1/budget/budgets/{budget_id}/send
  - POST /api/v1/budget/budgets/{budget_id}/send-reminder
  - POST /api/v1/budget/budgets/{budget_id}/set-public-code
  - POST /api/v1/budget/budgets/{budget_id}/unlock-public
  - PUT /api/v1/budget/budgets/{budget_id}
  - PUT /api/v1/budget/budgets/{budget_id}/items/{item_id}
related_permissions:
  - budget.read
  - budget.write
related_paths:
  - backend/app/modules/budget/frontend/pages/budgets/new.vue
  - backend/app/modules/budget/router.py
  - backend/app/modules/treatment_plan/frontend/components/budget/NewBudgetPlanHint.vue
last_verified_commit: 7a1637d
---

# Nuevo presupuesto

Formulario para crear un presupuesto **sin plan de tratamiento**. Al
guardar nace en estado `draft` y se abre el
[detalle](./budgets_id.md), donde se añaden las líneas.

## De un vistazo

- **Solo cabecera.** Aquí se elige paciente, validez y notas. Las
  líneas (ítems del catálogo, diente, descuentos, IVA) se añaden en el
  detalle después de guardar.
- **Si el paciente ya tiene un plan de tratamiento** en `draft` o
  `pending` sin presupuesto, el formulario lo avisa con un enlace al
  plan: el presupuesto de un plan se genera **desde el plan** (al
  confirmarlo) para que ambos queden vinculados y sincronizados. Un
  presupuesto creado aquí nunca se vincula al plan.
- **Numeración automática.** El número (`PRES-AAAA-####`) se asigna
  al guardar; no es editable.
- **Validez.** `valid_from` se propone a hoy; `valid_until` queda
  vacío (sin caducidad) salvo que lo rellenes.

## Crear un presupuesto

> Requiere `budget.write`.

1. Selecciona el paciente (si vienes de su ficha, vuelves a ella al
   cancelar).
2. Si aparece el aviso de plan sin presupuesto, pulsa **Ir al plan** y
   genera el presupuesto desde allí. Sigue solo si el presupuesto no
   corresponde a ningún plan.
3. Ajusta validez y notas (internas o visibles para el paciente).
4. **Crear y añadir ítems**. Se abre el detalle en `draft` para
   añadir líneas, enviar o firmar.

## Crear desde un plan de tratamiento

> Requiere `treatment_plan.plans.confirm`.

En el plan, pulsa **Confirmar**: se crea un presupuesto `draft`
vinculado con los tratamientos del plan como líneas. A partir de ahí
las líneas se gestionan desde el plan (ver
[detalle del presupuesto](./budgets_id.md#editar-líneas)).

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Crear el presupuesto | `budget.write` |
| Ver el aviso de planes sin presupuesto | `treatment_plan.plans.read` |

## Resolución de problemas

- **El selector de paciente está vacío.** No tienes el permiso
  `patients.read`.
- **No veo el aviso aunque el paciente tiene un plan.** Solo se avisa
  de planes en `draft`/`pending` sin presupuesto; un plan ya
  confirmado tiene su propio presupuesto en su detalle.

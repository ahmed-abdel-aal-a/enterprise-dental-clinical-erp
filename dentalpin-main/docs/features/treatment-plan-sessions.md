# Tratamientos multi-sesión con cobro fraccionado

**Fecha:** 2026-05-19
**Estado:** Implementado
**Módulos:** `catalog`, `treatment_plan`, `payments`
**Issue:** sin asignar

---

## 1. Contexto

En clínica real un mismo tratamiento (corona, endodoncia, etc.) se ejecuta en
varias sesiones y se cobra una parte por sesión (ej. corona: "Toma de medidas"
200€ + "Colocación" 600€ = 800€). Hasta esta entrega un
`PlannedTreatmentItem` solo soportaba un acto de completado y un único cobro
agregado, así que la única forma de modelar "cobro fraccionado" era duplicar
items o llevar la contabilidad por fuera del software.

Objetivos:

- Definir en el catálogo la plantilla de sesiones (nombre + precio) de cada
  tratamiento.
- Al añadir un tratamiento al plan, instanciar N sesiones con la misma forma
  pero independientes (snapshot).
- Marcar cada sesión completada con auditoría (quién, cuándo, notas).
- Que recepción vea, cuando el paciente sale del box, qué sesiones recién
  hechas faltan por cobrar y cobre con un click desde la pestaña Pagos.

---

## 2. Decisiones validadas

| Decisión | Elección |
|---|---|
| Plantilla en catálogo | Nueva tabla `CatalogItemSession` (label JSONB + `default_price`). |
| Validación catálogo | `Σ default_price == default_price` del item (tolerancia ±0.01) → 422 si falla. |
| Sesiones en plan | Nueva tabla `PlannedTreatmentItemSession` snapshot del template. |
| Importes por sesión | Variables (cada sesión puede tener precio distinto). |
| Granularidad cobro | FIFO virtual sobre `clinic_receivable`; sin FK Payment↔Session (ADR 0010). |
| Earned ledger | `PatientEarnedEntry` añade `source_session_id` (idempotencia `(treatment_id, session_id)`). |
| Evento publicado | Nuevo `treatment_plan.item_session_completed`; `treatment_completed` se conserva para recalls/odontograma pero **deja** de alimentar earned. |
| Items legacy | Backfill (`tp_0006`) crea 1 sesión por item con `amount = treatment.price_snapshot`. |
| Worklist multi-paciente | Fuera de alcance V1 (solo dentro de la ficha). |
| Sesión cancelada | Estado `cancelled` por sesión (no genera earned, no avanza item). |

---

## 3. Auditoría de arquitectura

| Riesgo | Veredicto |
|---|---|
| `manifest.depends` | Sin cambios. `treatment_plan` ya depende de `catalog`. `payments` sigue dependiendo solo de `patients` + `budget`. |
| FK cross-módulo | `PlannedTreatmentItemSession.completed_by → users.id` (users es global). Ninguna FK nueva hacia módulos externos. |
| Permisos | Reuso de `treatment_plan.plans.write`, `catalog.write`, `payments.record.write`. Cero nuevos. |
| Migraciones | Tres ramas independientes: `cat_0003`, `tp_0006` (con backfill), `pay_0002` (backfill tolerante). |
| Doble earned | Eliminada: payments deja de escuchar `treatment_plan.treatment_completed`; solo `item_session_completed` alimenta el ledger. |
| ADR 0010 | OK. "Pendiente de cobrar" surfacea `clinic_receivable`, no compara con factura. |

---

## 4. Cambios de datos

### 4.1 `catalog`
- Nuevo modelo `CatalogItemSession(id, catalog_item_id FK CASCADE, sequence, labels JSONB, default_price)`.
- Unique `(catalog_item_id, sequence)`.
- Migración: [`cat_0003_session_template.py`](../../backend/app/modules/catalog/migrations/versions/cat_0003_session_template.py).

### 4.2 `treatment_plan`
- Nuevo modelo `PlannedTreatmentItemSession(id, plan_item_id FK CASCADE, sequence, label, amount, status, completed_at, completed_by FK users, notes)`.
- Unique `(plan_item_id, sequence)`, índice `(plan_item_id, status)`.
- Migración: [`tp_0006_item_sessions.py`](../../backend/app/modules/treatment_plan/migrations/versions/tp_0006_item_sessions.py) — backfill 1 sesión por item existente con `amount = treatment.price_snapshot`.

### 4.3 `payments`
- `PatientEarnedEntry` añade `source_session_id` (UUID nullable) + `description` (String 160).
- Sustituye unique `(treatment_id)` por `(treatment_id, source_session_id)`.
- Migración: [`pay_0002_earned_session_id.py`](../../backend/app/modules/payments/migrations/versions/pay_0002_earned_session_id.py) — backfill tolerante vía `to_regclass` (no rompe deploys sin `treatment_plan` instalado).

---

## 5. Cambios de API

### 5.1 `catalog`
`POST /catalog/items` y `PUT /catalog/items/{id}` aceptan `sessions: list[CatalogItemSessionInput] | null`:
- Omitido → no se toca la plantilla.
- Lista (vacía o llena) → reemplaza atomically la plantilla (validación de suma vs `default_price`).

### 5.2 `treatment_plan`
Nuevos endpoints (todos requieren `treatment_plan.plans.write`):

| Método | Path | Acción |
|---|---|---|
| PATCH | `/items/{item_id}/sessions/{session_id}/complete` | Marcar sesión hecha. Publica `treatment_plan.item_session_completed`. |
| PATCH | `/items/{item_id}/sessions/{session_id}/cancel` | Cancelar sesión (no earned). |
| PUT | `/items/{item_id}/sessions/{session_id}` | Editar label / amount / notes (solo pending). |
| POST | `/items/{item_id}/sessions` | Añadir sesión manual. |
| DELETE | `/items/{item_id}/sessions/{session_id}` | Borrar sesión pending. |

`PATCH /items/{item_id}/complete` (legacy) sigue funcionando: completa la próxima sesión `pending`. Items con una sola sesión se comportan igual que antes.

### 5.3 `payments`
- `GET /payments/patients/{id}/pending-charges` — devuelve la lista FIFO de earned entries no cubiertas por net payments.

---

## 6. Cambios de frontend

| Capa | Cambios |
|---|---|
| `catalog` | `CatalogItemModal.vue` — sección colapsable "Sesiones (cobro fraccionado)" con editor + chip de validación suma. |
| `treatment_plan` | `PlanTreatmentList.vue` muestra chip de progreso "X/Y sesiones" en items multi-sesión; lista expandible con nuevo `PlanItemSessionRow.vue`. Composable `useTreatmentPlans` añade `completeSession` y `cancelSession`. |
| `payments` | Nuevo `PendingChargesCard.vue` al principio de `PatientPaymentsPanel.vue`; botón "Cobrar X €" abre `PaymentCreateModal` con `default-amount` prefijado. Composable `usePayments` añade `fetchPendingCharges`. |

---

## 7. Tests

### Backend

| Archivo | Cobertura |
|---|---|
| `tests/test_catalog.py` (4 nuevos) | Crear/editar template, validación suma 422, reemplazo atómico, omitir preserva. |
| `tests/test_treatment_plan.py` (7 nuevos) | Snapshot desde catálogo, fallback single-session, completar primera sesión no finaliza item, completar última sí, cancelación no produce earned, endpoint legacy avanza siguiente sesión, editar sesión completada 422. |
| `tests/modules/payments/test_pending_charges.py` (3 nuevos) | Unique `(treatment_id, session_id)`, FIFO parcial, vacío cuando todo cobrado. |

Regresión 76 tests pasan tras los cambios.

### Dogfood manual

1. Admin → Settings → Catálogo → crear "Corona" 800€ con 2 sesiones (200€ + 600€).
2. Dentista → crear plan paciente, añadir Corona en diente 26.
3. Verificar que el item muestra 2 sesiones pending y chip "0/2".
4. Marcar "Toma de medidas" completada.
5. Recepción → ficha paciente → pestaña Pagos → ver tarjeta "Pendiente de cobrar 200€".
6. Cobrar 200€ (efectivo). Tarjeta desaparece.
7. Días después: marcar "Colocación" completada. Cobrar 600€.
8. Verificar timeline con 2 earned + 2 payment; `clinic_receivable = 0`.

---

## 8. Documentación tocada

- `backend/app/modules/{catalog,treatment_plan,payments}/CHANGELOG.md` — entradas en `## Unreleased`.
- `backend/app/modules/{catalog,treatment_plan,payments}/CLAUDE.md` — nuevo gotcha + eventos consumidos/emitidos.
- `docs/features/treatment-plan-sessions.md` (este archivo).
- `docs/user-manual/{en,es}/treatment_plan/screens/plan-detail.md` — sesión en la lista de tratamientos.
- `docs/user-manual/{en,es}/payments/screens/patient-payments.md` — tarjeta "Pendiente de cobrar".

---

## 9. Plan de implementación (PRs realizados)

1. **PR1** — `catalog`: modelo, migración, schemas, servicio, admin UI, tests.
2. **PR2** — `treatment_plan`: modelo, migración con backfill, schemas, service refactor (`complete_session` + `_finalize_item`), endpoints, UI sesiones, tests.
3. **PR3** — `payments`: `source_session_id` en earned ledger, migración, handler `on_session_completed`, endpoint pending-charges, `PendingChargesCard`, tests.

---

## 10. Riesgos y rollback

| Riesgo | Mitigación |
|---|---|
| Backfill `tp_0006` lento en clínicas grandes | Una sola query con JOIN; los planes/items son tabla pequeña en la práctica clínica. |
| `pay_0002` corre antes de `tp_0006` | Backfill usa `to_regclass` → si la tabla aún no existe, deja la columna NULL. Idempotente. |
| Editar plantilla retroactivamente | Solo afecta a items nuevos; los ya creados conservan su snapshot. |
| Doble earned por compatibilidad | Handler legacy retirado en el mismo commit que añade el nuevo; el unique compuesto bloquea cualquier duplicado. |

---

## 11. Fuera de alcance V1

- Worklist multi-paciente "/payments/pending".
- Asignación explícita Payment ↔ Session (tabla puente).
- Duración por sesión + auto-creación de citas en agenda.
- Precio por sesión distinto según rol del doctor.
- KPI "promedio sesiones por tratamiento".

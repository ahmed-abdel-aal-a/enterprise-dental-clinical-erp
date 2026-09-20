# Plan técnico — Doctor por tratamiento dentro de un plan

**Fecha:** 2026-05-18
**Estado:** Aprobado (diseño UX validado, listo para implementar)
**Módulo:** `treatment_plan`
**Diseño UX previo:** `~/.claude/plans/en-los-planes-de-noble-diffie.md` (ephemeral; resumen replicado abajo)
**Issue:** sin asignar todavía

---

## 1. Contexto

Hoy `TreatmentPlan.assigned_professional_id` define un único doctor para todo el plan. En la práctica clínica distintos profesionales suelen ejecutar distintos tratamientos dentro del mismo plan (empaste por Dr A, endodoncia por Dr B). La feature añade un `assigned_professional_id` **por línea** (`PlannedTreatmentItem`), con tres requisitos:

1. Al añadir un item se asigna por defecto al doctor del plan.
2. Se puede cambiar el doctor del item sin fricción.
3. Dentro del plan se ve a primera vista qué doctor hace cada tratamiento cuando hay mezcla.

## 2. Decisiones validadas (de la fase de diseño)

| Decisión | Elección |
|---|---|
| Modelo herencia | **Snapshot por copia** al crear el item. Item es independiente del plan tras crearse. |
| Cascade al cambiar doctor del plan | **Confirm explícito** con opción "Reasignar pendientes". Solo reasigna los items pendientes cuyo `assigned_professional_id` coincidía con el doctor anterior del plan. Items completados nunca cambian. |
| Vista agrupada por doctor | **Fuera de V1**. Única lista, diferenciación por color del chip. |
| Roles en selector del item | **Dentistas + higienistas** (mismo criterio que el del plan, vía `useProfessionals()`). |

## 3. Auditoría de arquitectura

| Riesgo | Veredicto |
|---|---|
| Cross-module FK | `PlannedTreatmentItem.assigned_professional_id → users.id`. `users` es modelo core (no módulo). Precedente claro: `TreatmentPlan.assigned_professional_id` ya hace la misma referencia (`migrations/versions/tp_0001_initial.py:40-43`). Cumple. |
| Aislamiento de módulo (`manifest.depends`) | No se añaden dependencias. El módulo ya importa `users` indirectamente. |
| Permisos | No se introducen. Modificar `assigned_professional_id` de un item está cubierto por `treatment_plan.plans.write` (igual que añadir/quitar/reordenar items). |
| Migración | Nueva `tp_0005_item_assigned_professional`, `down_revision = "tp_0004"`, `branch_labels = None` (consistente con el resto de migraciones del módulo desde el squash). |
| Compatibilidad del evento `treatment_plan.treatment_added` | El payload es un dict serializable; el handler de `budget` lee claves concretas e ignora extras. Añadir `assigned_professional_id` es aditivo y seguro. |
| Estado del plan | Igual que `add_item` actual: solo se permite editar items si el plan no está locked por un `_is_plan_locked(plan)` (presupuesto activo). Reusamos la misma guard. |
| Multi-tenancy | El servicio filtra por `clinic_id` igual que el resto del módulo. El doctor seleccionado se valida contra `clinic_memberships` (ver §5.3) para evitar asignar usuarios de otra clínica. |
| Idempotencia / consistencia | El doctor del item se copia en `add_item`. Si el plan no tiene doctor, el item queda en `NULL`. Sin estado intermedio. |

Sin necesidad de ADR nueva. Es una extensión limitada del modelo existente.

## 4. Cambios de datos

### 4.1 Modelo (`backend/app/modules/treatment_plan/models.py`, clase `PlannedTreatmentItem` ~líneas 113-157)

Añadir columna y relación:

```python
assigned_professional_id: Mapped[UUID | None] = mapped_column(
    ForeignKey("users.id"), nullable=True, index=True
)
assigned_professional: Mapped["User | None"] = relationship(
    foreign_keys=[assigned_professional_id]
)
```

Y un índice compuesto para queries por doctor + plan:

```python
Index("idx_planned_items_plan_professional", "treatment_plan_id", "assigned_professional_id"),
```

### 4.2 Migración

`backend/app/modules/treatment_plan/migrations/versions/tp_0005_item_assigned_professional.py`:

```python
revision = "tp_0005"
down_revision = "tp_0004"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "planned_treatment_items",
        sa.Column("assigned_professional_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_planned_items_assigned_professional",
        "planned_treatment_items", "users",
        ["assigned_professional_id"], ["id"],
    )
    op.create_index(
        "ix_planned_treatment_items_assigned_professional_id",
        "planned_treatment_items", ["assigned_professional_id"],
    )
    op.create_index(
        "idx_planned_items_plan_professional",
        "planned_treatment_items",
        ["treatment_plan_id", "assigned_professional_id"],
    )

    # Backfill: items existentes heredan el doctor del plan padre.
    # Items completados se mantienen sin doctor planificado (su completed_by ya
    # registra quién lo ejecutó). Solo backfill de pendientes y cancelados.
    op.execute(
        """
        UPDATE planned_treatment_items pti
           SET assigned_professional_id = tp.assigned_professional_id
          FROM treatment_plans tp
         WHERE pti.treatment_plan_id = tp.id
           AND pti.assigned_professional_id IS NULL
           AND tp.assigned_professional_id IS NOT NULL
        """
    )

def downgrade():
    op.drop_index("idx_planned_items_plan_professional", "planned_treatment_items")
    op.drop_index("ix_planned_treatment_items_assigned_professional_id", "planned_treatment_items")
    op.drop_constraint("fk_planned_items_assigned_professional", "planned_treatment_items", type_="foreignkey")
    op.drop_column("planned_treatment_items", "assigned_professional_id")
```

> **Backfill:** todos los items existentes (pendientes y completados) heredan el doctor actual del plan. Esto da el punto de partida correcto sin sorpresas. Para items completados también lo poblamos para que las consultas históricas tengan un dato consistente; la UI sigue mostrando `completed_by` para ese caso.

## 5. Cambios de API

### 5.1 Schemas (`backend/app/modules/treatment_plan/schemas.py`)

```python
class PlannedTreatmentItemCreate(BaseModel):  # ~líneas 197-202
    treatment_id: UUID
    sequence_order: int | None = None
    notes: str | None = None
    assigned_professional_id: UUID | None = None  # NEW. Si null, se hereda del plan.


class PlannedTreatmentItemUpdate(BaseModel):  # ~líneas 205-209
    sequence_order: int | None = None
    notes: str | None = None
    assigned_professional_id: UUID | None = None  # NEW. Set explícito; null = quitar asignación.


class PlannedTreatmentItemResponse(BaseModel):  # ~líneas 212-232
    # ... campos existentes ...
    assigned_professional_id: UUID | None = None  # NEW
```

Y para la cascada en el modal de plan:

```python
class TreatmentPlanUpdate(BaseModel):  # ~líneas 87-93
    title: str | None = Field(default=None, max_length=200)
    assigned_professional_id: UUID | None = None
    diagnosis_notes: str | None = None
    internal_notes: str | None = None
    # NEW — al subir true, reasigna los items pendientes cuyo doctor coincidía
    # con el doctor anterior del plan. Campo write-only, no se persiste.
    reassign_pending_items: bool = False
```

> Importante: `PlannedTreatmentItemUpdate.assigned_professional_id` necesita un tratamiento especial porque hoy `update_item` filtra `if value is not None`. Para permitir **explícitamente unset** (asignar a `null`) hay que distinguir "no enviado" de "enviado como null". Solución mínima: usar un sentinel (`Field(default=...)`) con `model_dump(exclude_unset=True)` y aplicar manualmente. Detalle en §5.3.

### 5.2 Endpoints

No se añaden rutas nuevas. Los existentes ya cubren todo:

- `POST /treatment-plans/{id}/items` — acepta `assigned_professional_id` opcional.
- `PUT /treatment-plans/{id}/items/{item_id}` — acepta `assigned_professional_id` para override o unset.
- `PUT /treatment-plans/{id}` — acepta `reassign_pending_items: bool`.

### 5.3 Servicio (`service.py`)

#### `add_item` (~línea 382)

Justo antes de construir el `PlannedTreatmentItem`:

```python
# Default: hereda el doctor del plan. El cliente puede sobrescribir
# pasando explícitamente data["assigned_professional_id"].
assigned_professional_id = data.get("assigned_professional_id")
if assigned_professional_id is None:
    assigned_professional_id = plan.assigned_professional_id

if assigned_professional_id is not None:
    await _validate_professional_in_clinic(db, clinic_id, assigned_professional_id)

item = PlannedTreatmentItem(
    clinic_id=clinic_id,
    treatment_plan_id=plan_id,
    treatment_id=treatment_id,
    sequence_order=sequence_order,
    notes=data.get("notes"),
    assigned_professional_id=assigned_professional_id,  # NEW
)
```

Y propagar al payload del evento (línea 449-471):

```python
await event_bus.publish(
    "treatment_plan.treatment_added",
    {
        # ... claves existentes ...
        "assigned_professional_id": (
            str(item.assigned_professional_id) if item.assigned_professional_id else None
        ),  # NEW
    },
)
```

`_validate_professional_in_clinic` (helper nuevo, privado al módulo): query a `clinic_memberships` para confirmar que el `user_id` pertenece a la `clinic_id` con `role in ("dentist", "hygienist")`. Reusa `app.core.auth.permissions` si ya existe un helper similar; si no, escribir uno local.

#### `update_item` (~línea 475)

El bucle `for key, value in data.items(): if value is not None` ya no sirve para `assigned_professional_id` (queremos permitir set-to-null). Cambio:

```python
# Distinguir "no enviado" de "enviado como null" para campos nullables.
if "assigned_professional_id" in data:
    new_val = data["assigned_professional_id"]
    if new_val is not None:
        await _validate_professional_in_clinic(db, clinic_id, new_val)
    item.assigned_professional_id = new_val
    data = {k: v for k, v in data.items() if k != "assigned_professional_id"}

for key, value in data.items():
    if value is not None and hasattr(item, key):
        setattr(item, key, value)
```

El router debe pasar `data.model_dump(exclude_unset=True)` para que esto funcione.

#### `update` del plan (~línea 248) — cascada

```python
@staticmethod
async def update(db, clinic_id, plan_id, data):
    plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
    if not plan:
        return None

    reassign_pending = data.pop("reassign_pending_items", False)
    old_professional_id = plan.assigned_professional_id
    new_professional_id = data.get("assigned_professional_id", old_professional_id)

    if new_professional_id is not None and new_professional_id != old_professional_id:
        await _validate_professional_in_clinic(db, clinic_id, new_professional_id)

    for key, value in data.items():
        if value is not None and hasattr(plan, key):
            setattr(plan, key, value)

    # Cascade — solo cuando cambia el doctor y el cliente lo pide.
    if (
        reassign_pending
        and old_professional_id is not None
        and new_professional_id is not None
        and old_professional_id != new_professional_id
    ):
        await db.execute(
            update(PlannedTreatmentItem)
            .where(
                PlannedTreatmentItem.treatment_plan_id == plan_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
                PlannedTreatmentItem.status == "pending",
                PlannedTreatmentItem.assigned_professional_id == old_professional_id,
            )
            .values(assigned_professional_id=new_professional_id)
        )

    return plan
```

> Items con override (doctor distinto al anterior del plan) se respetan: el `WHERE assigned_professional_id == old_professional_id` los descarta. Items completados también se descartan (`status == "pending"`).

## 6. Cambios de frontend

### 6.1 Tipos (`frontend/app/types/index.ts` o equivalente en el layer)

```ts
export interface PlannedTreatmentItem {
  // ...campos existentes...
  assigned_professional_id: string | null
}

export interface PlannedTreatmentItemCreate {
  treatment_id: string
  sequence_order?: number
  notes?: string
  assigned_professional_id?: string | null
}

export interface PlannedTreatmentItemUpdate {
  sequence_order?: number
  notes?: string
  assigned_professional_id?: string | null
}

export interface TreatmentPlanUpdate {
  // ...campos existentes...
  reassign_pending_items?: boolean
}
```

### 6.2 `PlanTreatmentList.vue` (componente clave)

Ubicación: `backend/app/modules/treatment_plan/frontend/components/clinical/PlanTreatmentList.vue`.

Cambios:

- Añadir un **chip del doctor** entre el número de orden y el nombre del tratamiento (sección pendientes).
- Chip = `UAvatar` redondo con `getProfessionalColor(id)` de fondo + `getProfessionalInitials(id)` en blanco; tooltip con `getProfessionalFullName(id)`.
- Tamaño: 24px desktop, 32px ≤640px (cumple tap target).
- Estado sin doctor: `UIcon i-lucide-user-x` con `color="warning"`.
- **Click en el chip** abre un `UPopover` (desktop) o `USlideover` con `side="bottom"` (mobile, viewport <640px) con la lista de profesionales. Marca el actual. Botón superior "Usar doctor del plan" cuando hay override.
- Al seleccionar emite un nuevo evento `'item-doctor-change': [itemId, professionalId | null]`.
- Sección completados: chip muestra `completed_by`, no `assigned_professional_id`, con estilo apagado y tooltip de "Realizado por…".

Plantilla resumida (delta sobre el ítem pendiente actual ~líneas 250-318):

```vue
<div class="flex items-center gap-2 min-w-0">
  <button v-if="!readonly && localPending.length > 1" class="drag-handle ..." />
  <span class="text-subtle ... w-6 text-center shrink-0">{{ index + 1 }}.</span>

  <!-- NEW chip -->
  <PlanItemDoctorChip
    :item="item"
    :plan-professional-id="planProfessionalId"
    :readonly="readonly"
    @change="(professionalId) => emit('item-doctor-change', item.id, professionalId)"
  />

  <div class="min-w-0 flex-1">
    <div class="font-medium break-words">{{ getItemName(item) }}</div>
    <!-- tooth info … -->
  </div>
</div>
```

`PlanItemDoctorChip` queda como componente nuevo en el mismo folder, encapsulando el chip + popover/sheet. Tests visuales pueden vivir junto a la pantalla.

`PlanTreatmentList` recibe un prop nuevo `planProfessionalId: string | null` para saber cuándo el item está en "default" (mismo doctor) o "override" (distinto). No es necesario para el comportamiento, solo para el botón "Usar doctor del plan" del popover.

### 6.3 `TreatmentPlanModal.vue` (cascada al editar)

Ubicación: `backend/app/modules/treatment_plan/frontend/components/treatment-plans/TreatmentPlanModal.vue`.

Cuando se está editando un plan existente y el usuario cambia `form.assigned_professional_id` a un valor distinto del original **y** el plan tiene items pendientes con el doctor anterior:

1. Al pulsar Guardar, antes del `await updatePlan(...)`, se abre un `UModal` de confirmación secundario:

   > Tienes N tratamientos pendientes asignados a Dr X.
   > ¿Quieres reasignarlos también al nuevo doctor?
   > [Sí, reasignar] [No, dejar como están]

2. La respuesta setea `form.reassign_pending_items = true | false`.
3. Se llama a `updatePlan(plan.id, form)` que envía el flag al backend.

El conteo de pendientes (`N`) se calcula en el cliente a partir de los items que ya tiene cargados el plan (`plan.items`).

### 6.4 Modal/flow de "añadir tratamiento"

Multi-caller. La adición de items pasa por `useTreatmentPlans.addItem(planId, data)` (`composables/useTreatmentPlans.ts:202`). Callsites:

- `PlanDetailView.vue` (clinical)
- `PlansMode.vue`
- `TreatmentBar.vue` (odontogram)
- `PlannedTreatmentSelector.vue` (frontend/app/components/shared)

**Política**: el frontend **no envía** `assigned_professional_id` al añadir un item, salvo que la UI exponga explícitamente un selector. El backend lo hereda del plan. Esto mantiene los call-sites simples.

**Excepción** (opcional, evaluable tras la primera iteración): en el modal de añadir tratamiento de `PlanDetailView` exponer un `USelect` "Profesional" prellenado con el doctor del plan, visible siempre. Si el usuario lo cambia → se envía explícito. Si no lo toca → se omite del payload y el backend hereda.

> Recomendación de implementación: en V1.0 dejar la herencia silenciosa y permitir el override solo desde el chip de la lista (post-add). En V1.1 añadir el selector inline en el modal de add si la UX lo pide.

### 6.5 `useTreatmentPlans.ts`

Añadir helper:

```ts
async function changeItemDoctor(planId: string, itemId: string, professionalId: string | null) {
  return await updateItem(planId, itemId, { assigned_professional_id: professionalId })
}
```

Reusa el `updateItem` existente — no es endpoint nuevo, es atajo semántico.

### 6.6 i18n (`frontend/i18n/locales/{en,es}.json`)

Nuevas claves bajo `treatmentPlans.items`:

```json
{
  "treatmentPlans": {
    "items": {
      "assignedProfessional": "Assigned dentist",
      "assignedProfessionalAriaLabel": "Change assigned dentist for this treatment",
      "useUsersPlanDoctor": "Use plan's dentist",
      "noProfessional": "No dentist assigned",
      "inactiveProfessional": "Inactive professional",
      "cascadeReassign": {
        "title": "Reassign pending treatments?",
        "body": "You changed the plan dentist. {count} pending treatments were assigned to {previousName}. Do you want to reassign them to the new dentist as well?",
        "confirm": "Yes, reassign pending",
        "cancel": "No, keep as they are"
      }
    }
  }
}
```

Equivalentes en `es.json`.

## 7. Tests

### 7.1 Backend

`backend/app/modules/treatment_plan/tests/test_per_item_doctor.py` (nuevo):

- `test_add_item_inherits_plan_doctor` — sin override, item.assigned_professional_id == plan.assigned_professional_id.
- `test_add_item_with_explicit_doctor_overrides_plan` — override directo en el POST.
- `test_add_item_validates_doctor_belongs_to_clinic` — 422/400 si el user no es dentist/hygienist o no pertenece a la clínica.
- `test_add_item_plan_without_doctor_results_in_null` — plan sin doctor → item con null.
- `test_update_item_unset_doctor_to_null` — PUT con `assigned_professional_id: null` quita la asignación.
- `test_treatment_added_event_includes_doctor` — payload del evento contiene la clave.
- `test_update_plan_with_reassign_pending_cascades` — cascade afecta solo pendientes con el doctor anterior; no toca completados, no toca pendientes con override.
- `test_update_plan_without_reassign_flag_leaves_items` — flag falso → items intactos.
- `test_update_plan_doctor_validates_cascade_targets_only` — la cascada usa el doctor anterior real, no el que el cliente declara.

### 7.2 Frontend

- Component test (Vitest + @vue/test-utils) para `PlanItemDoctorChip` — render con doctor, sin doctor, popover abre/cierra, evento `change`.
- Component test para el confirm modal de cascade en `TreatmentPlanModal`.
- Snapshot de `PlanTreatmentList` con dos items de doctores distintos para validar diferenciación visual.

### 7.3 Manuales / dogfood

- `./scripts/reset-db.sh && ./scripts/seed-demo.sh && docker-compose up`.
- Crear plan con Dr A. Añadir 3 items → todos con chip de Dr A.
- Cambiar el chip del item 2 → Dr B. Verificar diferenciación de color.
- Editar el plan, cambiar doctor del plan a Dr C → confirm de cascade aparece con "2 tratamientos asignados a Dr A". Responder "Sí" → items 1 y 3 a Dr C, item 2 sigue siendo Dr B.
- En mobile 375px: bottom-sheet del selector de doctor del chip.
- Completar item 2 → chip muestra `completed_by` en estilo apagado.
- Plan sin doctor + añadir item → chip neutro con `i-lucide-user-x`.

## 8. Documentación (siguiendo la regla "When adding X, do Y")

Trigger: *"New endpoint"* no aplica (no se añaden). *"Touched a screen's behaviour or visuals"* → sí, varias pantallas.

| Acción | Archivo |
|---|---|
| Bump del CHANGELOG del módulo | `backend/app/modules/treatment_plan/CHANGELOG.md` (sección `## Unreleased`) |
| Screen MD bilingüe (EN + ES) | `docs/user-manual/{en,es}/treatment_plan/screens/treatment-plans_id.md` (sección "Asignar doctor por tratamiento") |
| Screen MD bilingüe — creación | `docs/user-manual/{en,es}/treatment_plan/screens/treatment-plans_new.md` (nota sobre herencia) |
| Bump de `last_verified_commit` | en ambos screen MD tras implementar |
| Eventos: añadir nota al payload | `docs/technical/treatment_plan/events.md` (campo `assigned_professional_id` en `treatment_plan.treatment_added`) |
| Catálogo de eventos auto-gen | Ejecutar `python backend/scripts/generate_catalogs.py` |
| Screenshots | `docs/screenshots/treatment_plan/plan-detail-mixed-doctors.png` (lista con dos doctores distintos), `plan-detail-cascade-confirm.png`, `plan-detail-doctor-popover.png`. Subirlos como parte del PR. |

## 9. Plan de implementación (PR sugeridos)

| PR | Alcance | Dependencias |
|---|---|---|
| **PR 1 — Backend** | Modelo + migración `tp_0005` + schemas + servicio (`add_item`, `update_item`, `update`/cascade) + helper `_validate_professional_in_clinic` + payload de evento + tests backend. | Ninguna. Se mergea solo (no rompe UI; el campo extra simplemente se ignora). |
| **PR 2 — Frontend lista (chip + popover)** | Tipos, `PlanItemDoctorChip`, integración en `PlanTreatmentList.vue`, i18n, tests de componente, screenshots. | PR 1. |
| **PR 3 — Frontend cascade modal** | Confirm secundario en `TreatmentPlanModal.vue`, i18n para cascade. | PR 1. Puede ir en paralelo a PR 2. |
| **PR 4 — Docs + screens MDs + CHANGELOG bump + regenerar catálogos** | Documentación user-manual EN/ES, events.md, generate_catalogs.py. | PR 1+2+3 ya en main. |

Cada PR es atómico, revisable y desplegable sin el siguiente.

## 10. Riesgos y rollback

- **Backfill incorrecto**: la migración popula items con el doctor del plan padre. Si un clínico ya tenía planes con doctor pero esperaba items sin asignar, podría sorprender. Mitigación: lo decimos explícitamente en el CHANGELOG y en el release note. Aceptable porque la app no está en prod y es el comportamiento más útil para clínicas existentes.
- **Cascade aplicada por error**: si el usuario marca "Sí, reasignar" por accidente, no hay undo automático. Mitigación: el modal de cascade enseña el número exacto y el nombre del doctor anterior para que la decisión sea consciente. Considerar un toast con "Deshacer" en V1.1.
- **Profesional desactivado**: items conservan el FK aunque el user esté `is_active=false`. La UI lo etiqueta como "Profesional inactivo" pero no bloquea editar el item para asignarlo a otro. Sin migración correctiva — el dato histórico se preserva.
- **Rollback DB**: `tp_0005` tiene `downgrade()` que dropea índice, FK y columna. Sin pérdida si se hace antes de que la UI escriba en producción.

## 11. Pendientes / fuera de alcance

- Doctor en el snapshot que `budget` consume hoy: **se propaga**. No bloquea, pero deja la puerta abierta a que `billing`/`payments` atribuyan por doctor en el futuro sin tener que re-emitir eventos pasados.
- Métricas / reportes por doctor desde plans. Fuera.
- Reasignar masivo con multi-select desde la lista. V2 si surge.
- Toggle Lista / Por doctor. Validado fuera de V1.
- Filtros UI de "qué doctor puede hacer qué tipo de tratamiento". Política clínica, no UI.

---

## Apéndice — Archivos tocados (referencia rápida)

Backend:
- `backend/app/modules/treatment_plan/models.py` (PlannedTreatmentItem)
- `backend/app/modules/treatment_plan/migrations/versions/tp_0005_item_assigned_professional.py` (nuevo)
- `backend/app/modules/treatment_plan/schemas.py`
- `backend/app/modules/treatment_plan/service.py` (`add_item`, `update_item`, `update`, helper de validación)
- `backend/app/modules/treatment_plan/router.py` (asegurar `model_dump(exclude_unset=True)` en los handlers de plan y item update)
- `backend/app/modules/treatment_plan/tests/test_per_item_doctor.py` (nuevo)

Frontend:
- `backend/app/modules/treatment_plan/frontend/components/clinical/PlanTreatmentList.vue`
- `backend/app/modules/treatment_plan/frontend/components/clinical/PlanItemDoctorChip.vue` (nuevo)
- `backend/app/modules/treatment_plan/frontend/components/treatment-plans/TreatmentPlanModal.vue`
- `backend/app/modules/treatment_plan/frontend/composables/useTreatmentPlans.ts` (atajo `changeItemDoctor`)
- `frontend/app/types/index.ts` (o el archivo de tipos del módulo)
- `frontend/i18n/locales/{en,es}.json`

Docs:
- `backend/app/modules/treatment_plan/CHANGELOG.md`
- `docs/user-manual/{en,es}/treatment_plan/screens/treatment-plans_id.md`
- `docs/user-manual/{en,es}/treatment_plan/screens/treatment-plans_new.md`
- `docs/technical/treatment_plan/events.md`
- `docs/screenshots/treatment_plan/*.png`

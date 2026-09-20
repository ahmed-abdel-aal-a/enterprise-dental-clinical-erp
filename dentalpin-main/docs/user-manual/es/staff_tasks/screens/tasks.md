---
module: staff_tasks
screen: tasks
route: /tasks
related_endpoints:
  - GET /api/v1/staff_tasks/
  - POST /api/v1/staff_tasks/
  - PATCH /api/v1/staff_tasks/{task_id}
  - DELETE /api/v1/staff_tasks/{task_id}
related_permissions:
  - staff_tasks.read
  - staff_tasks.write
related_paths:
  - backend/app/modules/staff_tasks/router.py
  - backend/app/modules/staff_tasks/frontend/pages/tasks/index.vue
last_verified_commit: c536b1f0
---

# Tareas del equipo

## Qué hace esta pantalla

- **Filtrar** por estado (Todas / Abierta / Reclamada / Hecha /
  Cancelada).
- **Nueva tarea**: modal con título, detalles, prioridad (Baja / Normal
  / Alta) y fecha límite opcional.
- **Los detalles** se muestran como segunda línea bajo el título; pasa
  el cursor para ver el texto completo.
- La columna **Asignada a** muestra quién tiene cada tarea.
- **Reclamar y cerrar en línea**: el selector de estado de cada fila
  solo ofrece los movimientos permitidos; reclamar una tarea sin asignar
  te asigna como responsable, y marcarla **Hecha** registra la hora de
  finalización. Reabrir una tarea reclamada la deja de nuevo disponible.
- Las tareas abiertas **vencidas** muestran la fecha límite en rojo.
- **Eliminar** con confirmación.
- **Paginación** en servidor, 20 filas por página.

## Estados

`Abierta → Reclamada → Hecha`, con `Cancelada` como salida. `Hecha` es
terminal (el selector pasa a ser una etiqueta). Un movimiento no
permitido devuelve 422 y muestra un aviso de error.

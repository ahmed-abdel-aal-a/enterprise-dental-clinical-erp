---
module: activity_journal
screen: journal
route: /journal
related_endpoints:
  - GET /api/v1/activity_journal
  - GET /api/v1/activity_journal/{entry_id}
related_permissions:
  - activity_journal.read
related_paths:
  - backend/app/modules/activity_journal/frontend/pages/journal/index.vue
last_verified_commit: 169054a
---

# Registro de actividad

Lista de solo lectura de todo lo registrado por el diario, de lo más
reciente a lo más antiguo. Cada fila muestra cuándo ocurrió, qué evento
la produjo, quién lo realizó (un guion indica que el evento no llevaba
usuario), el paciente afectado —con enlace a su ficha— y el espacio de
nombres del evento (origen). Los nombres de usuario y paciente se
resuelven en pantalla; si un nombre no puede resolverse (ficha
eliminada, o sin permiso para leerla) se muestra un id corto en su
lugar.

## Qué puedes hacer

- **Filtrar por tipo de evento**: elige uno de los tipos registrados en
  el desplegable (p. ej. `appointment.scheduled`, `budget.sent`).
- **Filtrar por rango de fechas**: limita a una ventana `Desde` / `Hasta`.
- **Paginar**: 20 filas por página mediante la barra de paginación.
- **Inspeccionar los datos**: usa el botón del ojo de una fila para
  ver, en modo lectura, la información exacta que transportaba el
  evento.

Las entradas no se pueden editar, eliminar ni crear manualmente: se
escriben automáticamente dentro de la transacción de la operación que
describen, por lo que el registro siempre coincide con lo que ocurrió
realmente.

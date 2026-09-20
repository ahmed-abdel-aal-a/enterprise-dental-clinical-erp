---
module: recalls
last_verified_commit: b1b82f5
---

# Recordatorios (recalls)

El módulo de recalls gestiona el flujo de **llamar al paciente para
que vuelva**: limpiezas, revisiones, control de ortodoncia,
seguimientos post-tratamiento, etc. Recepción marca a quién llamar
en qué mes, trabaja una lista de llamadas mensual, registra cada
intento y enlaza automáticamente la cita que el paciente acepta.

Recalls **no envía mensajes** por sí solo: solo organiza la cola y
publica eventos `recall.*` que un módulo futuro de comunicación
(WhatsApp, SMS, email) podrá consumir.

## Pantallas

- [Lista de llamadas](./screens/recalls.md) — listado mensual con
  filtros, contadores y acciones rápidas por fila.

## Referencia rápida

| Acción | Permiso requerido |
|--------|-------------------|
| Ver la lista, contadores y exportar CSV | `recalls.read` |
| Crear, snoozear, completar, enlazar cita | `recalls.write` |
| Borrar un recall | `recalls.delete` (admin) |
| Editar los ajustes (intervalos, mapeo) | `recalls.write` |

## Módulos relacionados

- **Pacientes** — los recalls están siempre asociados a un paciente.
  Si archivas el paciente o le marcas `do_not_contact`, sus recalls
  activos pasan a la cola **Necesita revisión** (no se borran).
- **Agenda** — al programar una cita para un paciente con recalls
  pendientes se enlaza automáticamente el más antiguo (si solo hay
  uno). Al completar la cita el recall pasa a *hecho*.
- **Planes de tratamiento** — el evento
  `treatment_plan.treatment_completed` activa una sugerencia de
  recall asociada al tratamiento (visible en *Próximas sugerencias*
  de la lista).
- **Odontograma** — botón *Programar recall* en cada tratamiento.
- **Notificaciones / outreach (futuro)** — consumirá los eventos
  `recall.created`, `recall.snoozed`, `recall.completed`,
  `recall.cancelled` para automatizar contactos.

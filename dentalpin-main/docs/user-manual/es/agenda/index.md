---
module: agenda
last_verified_commit: b1b82f5
---

# Agenda

El módulo de agenda gestiona las citas de la clínica: planificarlas,
moverlas, asignarlas a gabinete y profesional, y avanzarlas por el
flujo (programada → confirmada → en sala → completada → cobrada).
Es el centro operativo del día a día en recepción y consulta.

## Pantallas

- [Calendario y kanban](./screens/appointments.md) — vista semanal,
  diaria, kanban y vista móvil de un día. Crear, mover, redimensionar
  y cancelar citas desde la misma pantalla.

## Referencia rápida

| Acción | Permiso requerido |
|--------|-------------------|
| Ver el calendario y abrir citas | `agenda.appointments.read` |
| Crear, mover, redimensionar, cancelar | `agenda.appointments.write` |
| Avanzar el estado de una cita (transición) | `agenda.appointments.write` |
| Ver los gabinetes de la clínica | `agenda.cabinets.read` |
| Crear, renombrar o eliminar gabinetes | `agenda.cabinets.write` |
| Editar la nota clínica de una visita | `clinical_notes.notes.write` |

Los gabinetes se gestionan desde **Ajustes → Espacio de trabajo →
Gabinetes** (módulo *host*), no desde la propia agenda.

## Módulos relacionados

- **Pacientes** — toda cita pertenece a un paciente. Desde la ficha
  puedes navegar a su próxima cita.
- **Horarios (`schedules`)** — opcional. Cuando está instalado, calcula
  la disponibilidad real por profesional y gabinete; si lo desinstalas,
  la agenda cae a una franja por defecto 08:00–21:00.
- **Recalls** — al completar una cita aparece un modal de seguimiento
  que ofrece programar el próximo recall del paciente.
- **Planes de tratamiento** — desde un plan puedes saltar a la agenda
  con el paciente preseleccionado para programar la siguiente sesión.
- **Notificaciones** — se publican eventos `appointment.scheduled` /
  `appointment.status_changed` / `appointment.cabinet_changed` que
  otros módulos consumen para avisar al paciente.

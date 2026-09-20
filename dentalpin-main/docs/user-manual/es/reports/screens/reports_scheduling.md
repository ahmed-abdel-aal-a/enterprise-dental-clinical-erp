---
module: reports
screen: scheduling
route: /reports/scheduling
related_endpoints:
  - GET /api/v1/reports/scheduling/by-cabinet
  - GET /api/v1/reports/scheduling/by-day-of-week
  - GET /api/v1/reports/scheduling/by-professional
  - GET /api/v1/reports/scheduling/duration-variance
  - GET /api/v1/reports/scheduling/first-visits
  - GET /api/v1/reports/scheduling/funnel
  - GET /api/v1/reports/scheduling/punctuality
  - GET /api/v1/reports/scheduling/summary
  - GET /api/v1/reports/scheduling/waiting-times
related_permissions:
  - reports.scheduling.read
related_paths:
  - backend/app/modules/reports/frontend/pages/reports/scheduling.vue
  - backend/app/modules/reports/router.py
last_verified_commit: b1b82f5
---

# Informes de agenda y ocupación

Cuadro de mando de operativa de la agenda. Sirve para medir
*ocupación*, *no-shows*, *primeras visitas*, *puntualidad*,
*tiempos de espera* y la *variación de duración* (planificado vs
real) por profesional, gabinete y día de la semana.

## De un vistazo

- **Resumen** — citas totales, completadas, canceladas, no-show y
  porcentaje de ocupación del rango.
- **Por profesional** — número de citas, ocupación y tasa de
  no-show. Si tienes el módulo `schedules` instalado, la ocupación
  usa el horario real; si no, asume 08:00–21:00.
- **Por gabinete** — uso por sala. Útil para decidir reasignaciones.
- **Por día de la semana** — patrón semanal de carga. Identifica
  días flojos y días sobrecargados.
- **Funnel y primeras visitas** — del paciente nuevo a la primera
  cita y a la siguiente. Vista de captación.
- **Puntualidad y tiempos de espera** — diferencia entre la hora
  agendada y la hora de inicio real; tiempo medio de espera del
  paciente. Útil para mejorar la experiencia.
- **Variación de duración** — planificado vs real por
  profesional/tratamiento.

## Drill-downs

- Cada gráfica abre la agenda con el filtro de profesional /
  gabinete / rango aplicado.
- Para auditar un día concreto, usa la vista diaria de
  [/appointments](../../agenda/screens/appointments.md).

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Ver cualquiera de las secciones | `reports.scheduling.read` |
| Abrir la agenda (drill-down) | `agenda.appointments.read` |

## Resolución de problemas

- **Ocupación 100%.** La franja por defecto (08:00–21:00) sin
  `schedules` puede dar valores raros si el rango incluye días
  cerrados. Instala y configura `schedules` para una ocupación
  realista.
- **No aparece un profesional.** No tiene citas en el rango. Ajusta
  el rango o comprueba el filtro de profesional.
- **Puntualidad sin datos.** Las transiciones de cita (`in_room`,
  `completed`) no se están registrando en el día a día. Para que
  la métrica sea útil, recepción/consulta deben usar el botón de
  *En sala* al iniciar.

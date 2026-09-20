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

# Agenda and occupancy reports

Agenda operations dashboard. Used to measure *occupancy*,
*no-shows*, *first visits*, *punctuality*, *waiting times*, and the
*duration variance* (planned vs actual) per professional, room,
and day of week.

## At a glance

- **Summary** — total appointments, completed, cancelled,
  no-shows, and occupancy percentage for the range.
- **By professional** — appointment count, occupancy, and no-show
  rate. With the `schedules` module installed, occupancy uses real
  schedules; without it, it assumes 08:00–21:00.
- **By room** — usage per cabinet. Helpful for reassignment
  decisions.
- **By day of week** — weekly load pattern. Spots quiet and
  overloaded days.
- **Funnel and first visits** — from new patient to first
  appointment and the next one. Acquisition view.
- **Punctuality and waiting times** — difference between scheduled
  start and actual start; average patient wait time. Useful for UX
  improvements.
- **Duration variance** — planned vs actual per
  professional/treatment.

## Drill-downs

- Every chart opens the agenda with the professional / room /
  range filter applied.
- To audit a specific day, use the daily view of
  [/appointments](../../agenda/screens/appointments.md).

## Permissions

| What you see / can do | Permission |
|-----------------------|------------|
| View any of the sections | `reports.scheduling.read` |
| Open the agenda (drill-down) | `agenda.appointments.read` |

## Troubleshooting

- **100% occupancy.** The default window (08:00–21:00) without
  `schedules` can produce odd values if the range includes closed
  days. Install and configure `schedules` for realistic occupancy.
- **A professional is missing.** No appointments in the range.
  Adjust the range or check the professional filter.
- **Punctuality has no data.** Appointment transitions (`in_room`,
  `completed`) are not being logged day-to-day. For the metric to
  be useful, the front desk / clinic should use the *In-room*
  button at the start.

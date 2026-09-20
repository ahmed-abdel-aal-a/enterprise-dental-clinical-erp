---
module: reports
last_verified_commit: b1b82f5
---

# Informes

Hub de informes de la clínica. `reports` es un módulo **solo de
lectura** que agrega datos de los módulos de negocio (facturación,
presupuestos, agenda) y los presenta en cuadros de mando. Otros
módulos pueden añadir sus propios informes en el dashboard a través
del slot `reports.categories` — por ejemplo, `payments` añade el
informe de cobros (ver
[informes de cobros](../payments/screens/reports_payments.md)).

## Pantallas

- [Dashboard de informes](./screens/reports.md) — punto de entrada
  con tarjetas de cada familia de informe.
- [Facturación](./screens/reports_billing.md) — totales facturados,
  por serie, por método de pago, evolución.
- [Presupuestos](./screens/reports_budgets.md) — conversión, tiempo
  en cada estado, motivos de rechazo / cierre.
- [Agenda y ocupación](./screens/reports_scheduling.md) — horas
  ocupadas, no-shows, cancelaciones, mix de profesional.

## Referencia rápida

| Acción | Permiso requerido |
|--------|-------------------|
| Ver el dashboard | cualquiera de los tres permisos siguientes |
| Ver informes de facturación | `reports.billing.read` |
| Ver informes de presupuestos | `reports.budgets.read` |
| Ver informes de agenda | `reports.scheduling.read` |
| Ver informes de cobros (los aporta `payments`) | `payments.reports.read` |

## Módulos relacionados

- **Facturación, presupuestos, agenda** — fuentes de los informes
  agregados.
- **Cobros (`payments`)** — añade el cuadro de cobros vía el slot
  `reports.categories`.
- **Catálogo, pacientes** — referencias y enriquecimientos en filas
  agregadas (categoría del tratamiento, paciente, profesional).

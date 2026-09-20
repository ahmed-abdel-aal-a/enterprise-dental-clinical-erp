---
module: activity_journal
last_verified_commit: 03f4c5f1
---

# Registro de actividad

Diario de actividad del personal, de solo lectura y acumulativo: cada
evento suscrito de los módulos (citas, presupuestos, facturas, pagos,
pacientes, recalls, tratamientos, órdenes de laboratorio…) se registra
automáticamente con su autor, paciente, entidad de origen y datos
completos.

**Sensible por defecto**: solo `admin` ve el módulo inicialmente — el
registro indica qué miembro del equipo hizo qué. La clínica puede
conceder `activity_journal.read` a otros roles desde la interfaz de
administración de módulos. Las entradas nunca se pueden editar ni
eliminar.

## Pantallas

- [Registro de actividad](./screens/journal.md): filtros por tipo de
  evento y fechas, paginación y visor de datos por fila.

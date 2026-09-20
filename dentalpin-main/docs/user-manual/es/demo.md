# Documentación de los datos de demostración

Este documento describe los datos de demostración que crea el script de seed para probar y evaluar DentalPin.

## Puesta en marcha rápida

```bash
# Arrancar los servicios
docker-compose up -d

# Cargar los datos de demostración
./scripts/seed-demo.sh

# Abrir el navegador
open http://localhost:3000
```

## Credenciales de la demo

Todos los usuarios tienen la contraseña: **`demo1234`**

| Email | Rol | Nombre | Permisos |
|-------|-----|--------|----------|
| admin@demo.clinic | admin | Admin Demo | Acceso completo a todas las funciones |
| dentist@demo.clinic | dentist | Dra. María García López | Módulo clínico, sus propias citas |
| hygienist@demo.clinic | hygienist | Carlos López Martínez | Pacientes (lectura), citas |
| assistant@demo.clinic | assistant | Ana Martínez Ruiz | Pacientes, citas |
| receptionist@demo.clinic | receptionist | Laura Sánchez Pérez | Pacientes, citas |

### Probar cada rol

1. **Admin** - Puede acceder a Ajustes, gestionar usuarios y ver todos los datos
2. **Dentista** - Puede gestionar pacientes, ver/editar citas y ve el calendario profesional
3. **Higienista** - Puede ver pacientes y gestionar sus propias citas
4. **Asistente** - Puede gestionar pacientes y citas (sin acceso a ajustes)
5. **Recepcionista** - Igual que el asistente (flujo de recepción)

## Contenido de los datos de demostración

### Clínica

- **Nombre:** Clínica Dental Demo
- **NIF:** B12345678
- **Ubicación:** Calle Gran Vía 123, Madrid 28013
- **Gabinetes:** Gabinete 1 (azul), Gabinete 2 (verde)
- **Horario:** L-V 9:00-14:00, 16:00-20:00
- **Zona horaria:** Europe/Madrid

### Pacientes (15)

El seed incluye 15 pacientes con demografía variada:

| Paciente | Grupo de edad | Notas |
|----------|---------------|-------|
| Pablo Fernández | Niño (8) | Paciente pediátrico |
| Lucía Rodríguez | Adolescente (14) | Tratamiento de ortodoncia |
| Miguel González | Adulto joven (26) | - |
| Carmen Díaz | Adulta joven (29) | Sensibilidad dental |
| David Martín | Adulto (32) | - |
| Elena Ruiz | Adulta (39) | Embarazada, sin radiografías |
| Javier Sánchez | Adulto (44) | Diabético |
| Isabel López | Adulta (46) | - |
| Francisco García | Adulto (49) | Alergia a la penicilina |
| Rosa Martínez | Adulta (54) | Hipertensa |
| Antonio Hernández | Mayor (64) | Prótesis parcial |
| María Teresa Romero | Mayor (69) | Implantes |
| José Luis Muñoz | Mayor (74) | Con anticoagulantes |
| Dolores Vega | Mayor (76) | - |
| Manuel Castro | Mayor (79) | Prótesis completa |

### Citas (35-40)

Las citas se generan dinámicamente en relación con "hoy":

- **Semana pasada:** 10-12 citas (completadas, no presentado)
- **Semana actual:** 15-18 citas (programadas, confirmadas, en curso)
- **Próxima semana:** 10-12 citas (programadas)

**Tipos de tratamiento:**
- Revisión (30 min)
- Limpieza dental (45 min)
- Empaste (45 min)
- Extracción (60 min)
- Endodoncia (90 min)
- Ortodoncia - Revisión (30 min)
- Blanqueamiento (60 min)
- Implante - Consulta (45 min)
- Urgencia (30 min)

Las citas se reparten entre:
- Ambos profesionales (dentista e higienista)
- Ambos gabinetes
- Turnos de mañana (9:00-14:00) y de tarde (16:00-20:00)

## Referencia de scripts

### `./scripts/seed-demo.sh`

Carga la base de datos con los datos de demostración. Es seguro ejecutarlo varias veces (comprueba si ya existen datos).

```bash
./scripts/seed-demo.sh
```

### `./scripts/reset-db.sh`

Restablece la base de datos limpiando la versión de alembic y ejecutando las migraciones. NO carga datos.

```bash
./scripts/reset-db.sh
```

### `./scripts/setup-demo.sh`

Restablecimiento completo: limpia la base de datos Y carga los datos de demostración en un solo comando.

```bash
./scripts/setup-demo.sh
```

## Restablecer los datos de demostración

Para empezar de cero:

```bash
# Opción 1: restablecimiento completo
./scripts/setup-demo.sh

# Opción 2: pasos manuales
./scripts/reset-db.sh
./scripts/seed-demo.sh
```

## Personalizar los datos de demostración

Los datos de demostración se definen en `backend/app/seeds/demo_data.py`.

### Añadir pacientes

```python
# En la lista PATIENTS_DATA
{
    "id": UUID("..."),  # Generar un UUID nuevo
    "first_name": "Nombre",
    "last_name": "Apellidos",
    "phone": "+34 612 345 XXX",
    "email": "email@example.com",  # Opcional
    "date_of_birth": date(1990, 1, 1),
    "notes": "Notas clínicas",  # Opcional
},
```

### Añadir usuarios

```python
# En la lista USERS_DATA
{
    "id": UUID("..."),
    "email": "newuser@demo.clinic",
    "first_name": "Nombre",
    "last_name": "Apellidos",
    "role": "dentist",  # admin, dentist, hygienist, assistant, receptionist
    "membership_id": UUID("..."),
},
```

### Modificar la generación de citas

Edita la función `generate_appointments()` en `demo_data.py` para cambiar:
- Número de citas por semana
- Tipos de tratamiento
- Distribución de franjas horarias
- Distribución de estados

## Resolución de problemas

### «Demo data already exists»

El script de seed detecta datos existentes. Para restablecer:

```bash
./scripts/setup-demo.sh
```

### El inicio de sesión falla con credenciales válidas

El hash de la contraseña puede estar corrupto. Restablece y recarga:

```bash
./scripts/setup-demo.sh
```

### Las citas no aparecen en el calendario

1. Comprueba que estás viendo la semana correcta (las citas son relativas a hoy)
2. Verifica que el filtro de profesional no esté excluyendo citas
3. Comprueba el filtro de gabinete

### Errores de conexión a la base de datos

Asegúrate de que los servicios están en marcha:

```bash
docker-compose up -d
docker-compose ps  # Comprobar el estado
```

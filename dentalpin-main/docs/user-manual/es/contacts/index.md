---
module: contacts
last_verified_commit: 0a0651a
---

# Contactos

El módulo de contactos es el directorio de **proveedores externos** de
la clínica: laboratorios dentales, proveedores de material, delegados
comerciales y cualquier colaborador que no sea paciente ni personal.

Es un módulo opcional: un administrador lo activa desde
**Configuración → Módulos**. Una vez activo, **Contactos** aparece en
la barra lateral para los usuarios con permiso de lectura.

## Pantallas

- [Directorio de contactos](./screens/list.md) — lista con buscador,
  filtro por tipo y formulario de alta/edición.

## Referencia rápida

| Acción | Permiso necesario |
|--------|-------------------|
| Ver el directorio | `contacts.read` |
| Añadir, editar o desactivar un contacto | `contacts.write` |

Por defecto, dentistas e higienistas solo consultan el directorio;
auxiliares y recepción también lo gestionan.

## Conviene saber

- **Eliminar es desactivar.** Un contacto eliminado desaparece de la
  lista pero se conserva en la base de datos, de modo que los registros
  históricos que apunten a él (p. ej. futuros pedidos a laboratorio) se
  mantienen intactos.
- Tipos de contacto: **Laboratorio**, **Proveedor**, **Delegado**,
  **Otro**.

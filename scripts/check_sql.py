"""Verifica que Rossmix.sql tiene todas las secciones y campos requeridos."""
import os

BASE = os.path.dirname(os.path.dirname(__file__))
sql_path = os.path.join(BASE, 'scripts', 'database', 'Rossmix.sql')

with open(sql_path, 'r', encoding='utf-8') as f:
    sql = f.read()

secciones = [
    ('LIMPIEZA COMPLETA',            'Sección 1 — DROP tablas'),
    ('TIPOS ENUMERADOS',             'Sección 2 — ENUMs'),
    ('TABLA: USUARIO',               'Sección 3 — Tabla usuario'),
    ('TABLA: SERVICIOS',             'Sección 4 — Tabla servicios'),
    ('TABLA: EMPLEADOS',             'Sección 5 — Tabla empleados'),
    ('TABLA: EMPLEADO_SERVICIOS',    'Sección 6 — Many-to-many'),
    ('TABLA: HORARIOS_EMPLEADOS',    'Sección 7 — Horarios'),
    ('TABLA: CITAS',                 'Sección 8 — Tabla citas'),
    ('TABLA: PAGOS',                 'Sección 9 — Tabla pagos'),
    ('TABLA: NOTIFICACIONES',        'Sección 11 — Notificaciones'),
    ('TABLA: AUDITORIA_USUARIOS',    'Sección 12 — Auditoría'),
    ('DATOS INICIALES: SERVICIOS',   'Sección 14 — Datos servicios'),
    ('DATOS INICIALES: EMPLEADOS',   'Sección 15 — Datos empleados'),
    ('DATOS INICIALES: HORARIOS',    'Sección 17 — Datos horarios'),
    ('VERIFICACI',                    'Sección 18 — Verificación final'),
    ('TRIGGER: AUDIT',               'Sección 19 — Trigger auditoría'),
    ('VISTAS DE AUDIT',              'Sección 20 — Vistas auditoría'),
]

campos = [
    'token_gestion',
    'codigo_reserva    VARCHAR(20)',
    'notificaciones',
    'auditoria_usuarios',
    'fn_auditoria_nuevo_usuario',
    'trg_auditoria_nuevo_usuario',
    'vista_agenda_diaria',
    'vista_pagos_pendientes',
    'vista_nuevos_usuarios',
    'DROP FUNCTION IF EXISTS',
    'DROP VIEW  IF EXISTS vista_nuevos_usuarios',
    'pg_notify',
]

print("=" * 60)
print("  VERIFICACIÓN DE Rossmix.sql")
print("=" * 60)

print("\nSECCIONES:")
ok = fail = 0
for buscar, desc in secciones:
    found = buscar.upper() in sql.upper()
    estado = "OK  " if found else "FALTA"
    print(f"  {estado}  {desc}")
    if found: ok += 1
    else:     fail += 1
print(f"  Total: {ok} OK, {fail} faltantes")

print("\nELEMENTOS CLAVE:")
ok2 = fail2 = 0
for campo in campos:
    found = campo in sql
    estado = "OK  " if found else "FALTA"
    print(f"  {estado}  {campo}")
    if found: ok2 += 1
    else:     fail2 += 1
print(f"  Total: {ok2} OK, {fail2} faltantes")

lineas = sql.count('\n')
print(f"\nArchivo: {len(sql):,} caracteres | {lineas:,} líneas")
print("\n" + "=" * 60)

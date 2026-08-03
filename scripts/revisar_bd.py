"""Revisión completa de la base de datos del proyecto Rossmix."""
import os, sys
from dotenv import load_dotenv
load_dotenv()

try:
    import psycopg
except ImportError:
    sys.exit("Falta psycopg. Ejecuta: pip install psycopg[binary]")

conn = psycopg.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', '5432'),
    dbname=os.environ.get('DB_NAME', 'Rossmix'),
    user=os.environ.get('DB_USER', 'postgres'),
    password=os.environ.get('DB_PASSWORD', ''),
)
cur = conn.cursor()

def sep(titulo):
    print(f"\n{'='*58}")
    print(f"  {titulo}")
    print('='*58)

# ── Tablas y conteos ─────────────────────────────────────
sep("TABLAS EN POSTGRESQL")
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tablas = [r[0] for r in cur.fetchall()]
for tabla in tablas:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        print(f"  {tabla:35} {cur.fetchone()[0]:>5} registros")
    except Exception:
        print(f"  {tabla:35} (no accesible)")

# ── Usuarios ─────────────────────────────────────────────
sep("USUARIOS REGISTRADOS")
cur.execute("SELECT id, nombre, email, tipo_usuario, activo FROM usuario ORDER BY tipo_usuario, nombre")
for r in cur.fetchall():
    estado = "activo" if r[4] else "inactivo"
    print(f"  #{r[0]:3} [{r[3]:7}] {r[1]:25} {r[2]:35} {estado}")

# ── Servicios ─────────────────────────────────────────────
sep("SERVICIOS")
cur.execute("SELECT id_servicio, nombre_servicio, precio_total, duracion_minutos, activo FROM servicios ORDER BY nombre_servicio")
for r in cur.fetchall():
    estado = "activo" if r[4] else "inactivo"
    print(f"  #{r[0]:2} {r[1]:40} ${float(r[2]):>10,.0f} COP  {r[3]} min  {estado}")

# ── Empleados ─────────────────────────────────────────────
sep("EMPLEADOS")
cur.execute("SELECT id_empleado, nombre, especialidad, activo FROM empleados ORDER BY nombre")
for r in cur.fetchall():
    estado = "activo" if r[3] else "inactivo"
    esp = str(r[2] or 'Sin especialidad')[:30]
    print(f"  #{r[0]:2} {r[1]:25} {esp:30} {estado}")

# ── Horarios por empleado ──────────────────────────────────
sep("HORARIOS POR EMPLEADO")
dias = {0:'Dom',1:'Lun',2:'Mar',3:'Mie',4:'Jue',5:'Vie',6:'Sab'}
cur.execute("""
    SELECT e.nombre, h.dia_semana, h.hora_inicio, h.hora_fin
    FROM horarios_empleados h
    JOIN empleados e ON h.id_empleado = e.id_empleado
    ORDER BY e.nombre, h.dia_semana
""")
emp_actual = None
for r in cur.fetchall():
    if r[0] != emp_actual:
        print(f"\n  {r[0]}:")
        emp_actual = r[0]
    dia = dias.get(r[1], str(r[1]))
    print(f"    {dia}: {str(r[2])[:5]} — {str(r[3])[:5]}")

# ── Citas ──────────────────────────────────────────────────
sep("CITAS (TODAS)")
cur.execute("""
    SELECT c.id_cita, u.nombre, s.nombre_servicio, e.nombre,
           c.estado, c.fecha_hora_inicio, c.monto_total, c.monto_abono, c.saldo_pendiente
    FROM citas c
    JOIN usuario  u ON c.id_cliente  = u.id
    JOIN servicios s ON c.id_servicio = s.id_servicio
    LEFT JOIN empleados e ON c.id_empleado = e.id_empleado
    ORDER BY c.fecha_hora_inicio DESC
""")
rows = cur.fetchall()
print(f"  Total: {len(rows)} citas\n")
for r in rows:
    emp = str(r[3] or 'Sin asignar')[:18]
    print(f"  #{r[0]:3} {r[1]:20} | {r[2]:30} | {emp:18} | [{r[4]:15}] | {r[5].strftime('%d/%m/%Y %H:%M')} | ${float(r[6] or 0):>8,.0f}")

# ── Estadísticas de estados de citas ──────────────────────
sep("ESTADÍSTICAS DE CITAS")
cur.execute("SELECT estado, COUNT(*) FROM citas GROUP BY estado ORDER BY estado")
for r in cur.fetchall():
    print(f"  {r[0]:20} {r[1]:>3} cita(s)")

# ── Pagos ──────────────────────────────────────────────────
sep("PAGOS REGISTRADOS")
cur.execute("""
    SELECT p.id_pago, u.nombre, p.monto, p.metodo_pago, p.estado_pago, p.fecha_pago
    FROM pagos p
    JOIN citas c  ON p.id_cita   = c.id_cita
    JOIN usuario u ON c.id_cliente = u.id
    ORDER BY p.fecha_pago DESC
    LIMIT 10
""")
pagos = cur.fetchall()
if pagos:
    for r in pagos:
        print(f"  #{r[0]:3} {r[1]:20} ${float(r[2]):>8,.0f} COP  {r[3]:15} [{r[4]}]  {r[5].strftime('%d/%m/%Y %H:%M')}")
else:
    print("  Sin pagos registrados")

# ── Trigger de auditoría ──────────────────────────────────
sep("AUDITORÍA DE USUARIOS (últimos 5)")
try:
    cur.execute("SELECT id_usuario, nombre, email, tipo_usuario, fecha_registro FROM auditoria_usuarios ORDER BY fecha_registro DESC LIMIT 5")
    audits = cur.fetchall()
    if audits:
        for r in audits:
            print(f"  ID:{r[0]:3} {r[1]:25} {r[2]:35} {r[3]:7} {r[4].strftime('%d/%m/%Y %H:%M')}")
    else:
        print("  Sin registros de auditoría aún")
except Exception as e:
    print(f"  (tabla auditoria_usuarios no disponible: {e})")

# ── Trigger en PostgreSQL ─────────────────────────────────
sep("TRIGGERS EN POSTGRESQL")
cur.execute("""
    SELECT trigger_name, event_manipulation, event_object_table
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
    ORDER BY trigger_name
""")
triggers = cur.fetchall()
if triggers:
    for r in triggers:
        print(f"  {r[0]:40} {r[1]:8} ON {r[2]}")
else:
    print("  Sin triggers definidos")

conn.close()

print("\n" + "="*58)
print("  REVISIÓN BD COMPLETADA")
print("="*58 + "\n")

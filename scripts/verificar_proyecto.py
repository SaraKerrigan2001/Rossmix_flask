"""Verificación completa del proyecto Rossmix Flask."""
import os, ast, re, sys

BASE = os.path.dirname(os.path.dirname(__file__))

def seccion(titulo):
    print(f"\n{'='*55}")
    print(f"  {titulo}")
    print('='*55)

# ── 1. Dependencias ─────────────────────────────────────
seccion("1. DEPENDENCIAS")
libs = [
    ('flask','Flask'), ('flask_sqlalchemy','Flask-SQLAlchemy'),
    ('werkzeug','Werkzeug'), ('psycopg','psycopg'),
    ('openpyxl','openpyxl'), ('reportlab','reportlab'),
    ('uuid','uuid'), ('secrets','secrets'), ('dataclasses','dataclasses'),
]
for mod, name in libs:
    try:
        __import__(mod)
        print(f"  OK    {name}")
    except ImportError:
        print(f"  FALTA {name}")

# ── 2. Sintaxis app.py ──────────────────────────────────
seccion("2. SINTAXIS app.py")
app_path = os.path.join(BASE, 'app.py')
with open(app_path, 'r', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
    print("  OK    Sintaxis correcta")
except SyntaxError as e:
    print(f"  ERROR línea {e.lineno}: {e.msg}")
    sys.exit(1)

# ── 3. Clases de arquitectura ───────────────────────────
seccion("3. CLASES DE ARQUITECTURA")
clases = [
    'PasarelaPagoService','ReservaService','EstadoReserva','ClienteDTO',
    'ReservaError','SistemaAgendaDiaria','CitaDiaria','EstadoCitaOperativa',
    'MetodoPagoSaldo','InvalidOperationError',
    'SistemaGestionCitas','ReprogramacionError','ServicioNotificaciones',
]
for c in clases:
    found = bool(re.search(rf'^class {c}[:(]', src, re.MULTILINE))
    print(f"  {'OK  ' if found else 'FALTA'} {c}")

# ── 4. Rutas registradas ────────────────────────────────
seccion("4. RUTAS REGISTRADAS")
rutas = re.findall(r"@app\.route\('([^']+)'", src)
print(f"  Total: {len(rutas)} rutas")
for r in sorted(rutas):
    print(f"  {r}")

# ── 5. Funciones duplicadas ─────────────────────────────
seccion("5. FUNCIONES DUPLICADAS")
funcs = re.findall(r'^def (\w+)\(', src, re.MULTILINE)
seen  = {}
for f in funcs:
    seen[f] = seen.get(f, 0) + 1
dups = {k:v for k,v in seen.items() if v > 1}
if dups:
    for k,v in dups.items():
        print(f"  DUPLICADA: {k} ({v} veces)")
else:
    print("  OK    Ninguna duplicada")

# ── 6. url_for sin función ──────────────────────────────
seccion("6. url_for REFERENCIAS")
url_fors = set(re.findall(r"url_for\('(\w+)'", src))
defined  = set(re.findall(r'^def (\w+)\(', src, re.MULTILINE))
missing  = url_fors - defined - {'static'}
if missing:
    print(f"  SIN FUNCION: {missing}")
else:
    print(f"  OK    Todas las referencias válidas ({len(url_fors)} url_for)")

# ── 7. Templates ────────────────────────────────────────
seccion("7. TEMPLATES")
templates = [
    'base.html','index.html','login.html','registro.html',
    'dashboard_admin.html','dashboard_cliente.html','notificaciones.html',
    'test_image.html',
    'citas/paso1_servicio.html','citas/paso2_empleado.html',
    'citas/paso3_fecha_hora.html','citas/paso4_confirmacion.html',
    'citas/confirmada.html','citas/mis_citas.html',
    'citas/cliente_pagos_form.html','citas/gestionar_cita.html',
    'citas/reprogramar.html',
    'admin/citas.html','admin/empleados.html','admin/empleados_form.html',
    'admin/servicios.html','admin/servicios_form.html',
    'admin/clientes.html','admin/clientes_form.html',
    'admin/horarios.html','admin/horarios_form.html',
    'admin/pagos.html','admin/pagos_form.html',
    'admin/pagos_confirmar.html','admin/agenda_diaria.html',
]
tpl_base = os.path.join(BASE, 'app', 'templates')
ok = fail = 0
for t in templates:
    path = os.path.join(tpl_base, t)
    if os.path.exists(path):
        print(f"  OK    {t}")
        ok += 1
    else:
        print(f"  FALTA {t}")
        fail += 1
print(f"  Total: {ok} OK, {fail} faltantes")

# ── 8. Imágenes ─────────────────────────────────────────
seccion("8. IMÁGENES NAILS")
nails_dir = os.path.join(BASE, 'app', 'static', 'images', 'nails')
ok = fail = 0
for f in sorted(os.listdir(nails_dir)):
    path = os.path.join(nails_dir, f)
    with open(path, 'rb') as fp:
        h = fp.read(3)
    if h[:2] == b'\xff\xd8':   tipo = 'JPEG'
    elif h[:2] == b'\x89P':    tipo = 'PNG '
    elif h[:3] == b'GIF':      tipo = 'GIF '
    else:                      tipo = 'INVAL'
    size = round(os.path.getsize(path)/1024, 1)
    marca = 'OK  ' if tipo != 'INVAL' else 'FALTA'
    if tipo != 'INVAL': ok += 1
    else:               fail += 1
    print(f"  {marca} {tipo}  {size:>7} KB  {f}")
print(f"  Total: {ok} OK, {fail} inválidas")

# ── 9. BD modelo Cita — campos clave ────────────────────
seccion("9. MODELO Cita — CAMPOS CLAVE")
campos = ['token_gestion','codigo_reserva','estado','monto_abono',
          'saldo_pendiente','notas','fecha_hora_inicio','fecha_hora_fin']
for campo in campos:
    found = campo in src
    print(f"  {'OK  ' if found else 'FALTA'} Cita.{campo}")

print("\n" + "="*55)
print("  VERIFICACIÓN COMPLETADA")
print("="*55 + "\n")

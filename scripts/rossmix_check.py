"""
ROSSMIX -- SCRIPT DE VERIFICACION COMPLETA

Unifica en un solo comando todos los chequeos del proyecto:
  1. Dependencias Python
  2. Sintaxis y arquitectura de app.py
  3. Templates y rutas
  4. Imagenes
  5. Base de datos PostgreSQL (tablas, datos, triggers)
  6. Seguridad (credenciales hardcodeadas, .env en Git)
  7. Rossmix.sql (secciones y campos clave)
  8. Correccion de precios incorrectos (fix_price)
  9. Trigger de auditoria (instalacion si no existe)

Uso:
  python scripts/rossmix_check.py            (todo)
  python scripts/rossmix_check.py --bd       (solo BD)
  python scripts/rossmix_check.py --code     (solo codigo)
  python scripts/rossmix_check.py --fix      (fix precios)
  python scripts/rossmix_check.py --trigger  (instalar trigger)
"""
import os, ast, re, sys, subprocess

# ── Configuración base ────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE, '.env'))
except ImportError:
    pass


# ═════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═════════════════════════════════════════════════════════════════════════════

ERRORES  = []
WARNINGS = []

def titulo(texto):
    linea = '=' * 62
    print(f"\n{linea}")
    print(f"  {texto}")
    print(linea)

def ok(msg):    print(f"  OK   {msg}")
def falta(msg): print(f"  FAIL {msg}"); ERRORES.append(msg)
def warn(msg):  print(f"  WARN {msg}"); WARNINGS.append(msg)

def resumen_final():
    print(f"\n{'='*62}")
    print(f"  RESULTADO FINAL")
    print(f"{'='*62}")
    if not ERRORES and not WARNINGS:
        print("  TODO CORRECTO -- el proyecto esta en perfecto estado.")
    else:
        if ERRORES:
            print(f"\n  Errores ({len(ERRORES)}):")
            for e in ERRORES:
                print(f"    FAIL  {e}")
        if WARNINGS:
            print(f"\n  Avisos ({len(WARNINGS)}):")
            for w in WARNINGS:
                print(f"    WARN  {w}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 1 — DEPENDENCIAS PYTHON
# ═════════════════════════════════════════════════════════════════════════════

def check_dependencias():
    titulo("1. DEPENDENCIAS PYTHON")
    libs = [
        ('flask',           'Flask'),
        ('flask_sqlalchemy','Flask-SQLAlchemy'),
        ('werkzeug',        'Werkzeug'),
        ('psycopg',         'psycopg'),
        ('openpyxl',        'openpyxl'),
        ('reportlab',       'reportlab'),
        ('dotenv',          'python-dotenv'),
        ('uuid',            'uuid'),
        ('secrets',         'secrets'),
        ('dataclasses',     'dataclasses'),
    ]
    for mod, name in libs:
        try:
            __import__(mod)
            ok(name)
        except ImportError:
            falta(f"Dependencia faltante: {name}  →  pip install {name}")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 2 — CÓDIGO: SINTAXIS, ARQUITECTURA, RUTAS, TEMPLATES, IMÁGENES
# ═════════════════════════════════════════════════════════════════════════════

def check_codigo():
    app_path = os.path.join(BASE, 'app.py')
    with open(app_path, 'r', encoding='utf-8') as f:
        src = f.read()

    # ── Sintaxis ──────────────────────────────────────────────────────────
    titulo("2. SINTAXIS DE app.py")
    try:
        ast.parse(src)
        ok("Sintaxis correcta")
    except SyntaxError as e:
        falta(f"Error de sintaxis en línea {e.lineno}: {e.msg}")
        return

    # ── Clases de arquitectura ────────────────────────────────────────────
    titulo("3. CLASES DE ARQUITECTURA")
    clases = [
        'PasarelaPagoService', 'ReservaService', 'EstadoReserva', 'ClienteDTO',
        'ReservaError', 'SistemaAgendaDiaria', 'CitaDiaria', 'EstadoCitaOperativa',
        'MetodoPagoSaldo', 'InvalidOperationError',
        'SistemaGestionCitas', 'ReprogramacionError', 'ServicioNotificaciones',
    ]
    for c in clases:
        if re.search(rf'^class {c}[:(]', src, re.MULTILINE):
            ok(c)
        else:
            falta(f"Clase no encontrada: {c}")

    # ── Rutas ─────────────────────────────────────────────────────────────
    titulo("4. RUTAS REGISTRADAS")
    rutas = re.findall(r"@app\.route\('([^']+)'", src)
    ok(f"{len(rutas)} rutas registradas")
    for r in sorted(rutas):
        print(f"       {r}")

    # ── Funciones duplicadas ──────────────────────────────────────────────
    titulo("5. FUNCIONES DUPLICADAS")
    funcs = re.findall(r'^def (\w+)\(', src, re.MULTILINE)
    seen  = {}
    for f in funcs:
        seen[f] = seen.get(f, 0) + 1
    dups = {k: v for k, v in seen.items() if v > 1}
    if dups:
        for k, v in dups.items():
            falta(f"Función duplicada: {k} ({v} veces)")
    else:
        ok("Ninguna función duplicada")

    # ── url_for referencias ───────────────────────────────────────────────
    titulo("6. REFERENCIAS url_for")
    url_fors = set(re.findall(r"url_for\('(\w+)'", src))
    defined  = set(re.findall(r'^def (\w+)\(', src, re.MULTILINE))
    missing  = url_fors - defined - {'static'}
    if missing:
        for m in missing:
            falta(f"url_for sin función: {m}")
    else:
        ok(f"Todas las referencias válidas ({len(url_fors)} url_for)")

    # ── Templates ─────────────────────────────────────────────────────────
    titulo("7. TEMPLATES HTML")
    templates = [
        'base.html', 'index.html', 'login.html', 'registro.html',
        'dashboard_admin.html', 'dashboard_cliente.html', 'notificaciones.html',
        'citas/paso1_servicio.html', 'citas/paso2_empleado.html',
        'citas/paso3_fecha_hora.html', 'citas/paso4_confirmacion.html',
        'citas/confirmada.html', 'citas/mis_citas.html',
        'citas/cliente_pagos_form.html', 'citas/gestionar_cita.html',
        'citas/reprogramar.html',
        'admin/citas.html', 'admin/empleados.html', 'admin/empleados_form.html',
        'admin/servicios.html', 'admin/servicios_form.html',
        'admin/clientes.html', 'admin/clientes_form.html',
        'admin/horarios.html', 'admin/horarios_form.html',
        'admin/pagos.html', 'admin/pagos_form.html',
        'admin/pagos_confirmar.html', 'admin/agenda_diaria.html',
    ]
    tpl_base = os.path.join(BASE, 'app', 'templates')
    ok_t = fail_t = 0
    for t in templates:
        path = os.path.join(tpl_base, t)
        if os.path.exists(path):
            ok(t); ok_t += 1
        else:
            falta(f"Template faltante: {t}"); fail_t += 1
    print(f"\n  Total: {ok_t} OK, {fail_t} faltantes")

    # ── Imágenes ───────────────────────────────────────────────────────────
    titulo("8. IMÁGENES NAILS")
    nails_dir = os.path.join(BASE, 'app', 'static', 'images', 'nails')
    ok_i = fail_i = 0
    for f in sorted(os.listdir(nails_dir)):
        path = os.path.join(nails_dir, f)
        with open(path, 'rb') as fp:
            h = fp.read(3)
        if h[:2] == b'\xff\xd8':  tipo = 'JPEG'
        elif h[:2] == b'\x89P':   tipo = 'PNG'
        elif h[:3] == b'GIF':     tipo = 'GIF'
        else:                     tipo = 'INVAL'
        size = round(os.path.getsize(path) / 1024, 1)
        if tipo != 'INVAL':
            ok(f"{tipo}  {size:>7} KB  {f}"); ok_i += 1
        else:
            warn(f"Imagen inválida (HTML/otro): {f}  →  reemplazar con JPEG real"); fail_i += 1
    print(f"\n  Total: {ok_i} OK, {fail_i} inválidas")

    # ── Campos clave del modelo Cita ────────────────────────────────────────
    titulo("9. MODELO Cita — CAMPOS CLAVE")
    campos = ['token_gestion', 'codigo_reserva', 'estado', 'monto_abono',
              'saldo_pendiente', 'notas', 'fecha_hora_inicio', 'fecha_hora_fin']
    for campo in campos:
        if campo in src:
            ok(f"Cita.{campo}")
        else:
            falta(f"Campo no encontrado en modelo: Cita.{campo}")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 3 — SEGURIDAD
# ═════════════════════════════════════════════════════════════════════════════

def check_seguridad():
    titulo("10. SEGURIDAD — CREDENCIALES Y GIT")
    app_path = os.path.join(BASE, 'app.py')
    with open(app_path, 'r', encoding='utf-8') as f:
        src = f.read()

    checks = [
        ('postgres:1234',                       "Contraseña de BD hardcodeada: postgres:1234"),
        ("SECRET_KEY = 'tu_clave",              "SECRET_KEY hardcodeada en app.py"),
        ("generate_password_hash('admin123')",  "Contraseña admin123 hardcodeada"),
        ('password="1234"',                     'password=1234 hardcodeada'),
        ("password='1234'",                     "password=1234 hardcodeada"),
    ]
    alguno = False
    for patron, desc in checks:
        if patron in src:
            falta(desc); alguno = True
    if not alguno:
        ok("Sin credenciales hardcodeadas en app.py")

    r1 = subprocess.run(['git', 'ls-files', '.env'],
                        capture_output=True, text=True, cwd=BASE)
    if r1.stdout.strip():
        falta(".env está trackeado en Git — puede exponer contraseñas")
    else:
        ok(".env NO está en Git")

    r2 = subprocess.run(['git', 'ls-files', '.env.example'],
                        capture_output=True, text=True, cwd=BASE)
    if r2.stdout.strip():
        ok(".env.example sí está en Git")
    else:
        warn(".env.example no está en Git — recomendable incluirlo")

    # Variables de entorno cargadas
    vars_req = ['SECRET_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME',
                'ADMIN_EMAIL', 'ADMIN_PASSWORD']
    print()
    for v in vars_req:
        val = os.environ.get(v)
        if val:
            masked = '***' if 'PASSWORD' in v or 'KEY' in v else val
            ok(f"{v} = {masked}")
        else:
            warn(f"Variable de entorno no definida: {v}")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 4 — BASE DE DATOS
# ═════════════════════════════════════════════════════════════════════════════

def check_bd():
    titulo("11. CONEXIÓN A POSTGRESQL")
    try:
        import psycopg
    except ImportError:
        falta("psycopg no instalado"); return

    try:
        conn = psycopg.connect(
            host    = os.environ.get('DB_HOST', 'localhost'),
            port    = os.environ.get('DB_PORT', '5432'),
            dbname  = os.environ.get('DB_NAME', 'Rossmix'),
            user    = os.environ.get('DB_USER', 'postgres'),
            password= os.environ.get('DB_PASSWORD', ''),
        )
        ok("Conexión exitosa a PostgreSQL")
    except Exception as e:
        falta(f"No se pudo conectar a PostgreSQL: {e}")
        return

    cur = conn.cursor()

    # Tablas y conteos
    titulo("12. TABLAS Y REGISTROS")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    tablas = [r[0] for r in cur.fetchall()]
    tablas_requeridas = ['usuario', 'servicios', 'empleados', 'empleado_servicios',
                         'horarios_empleados', 'citas', 'pagos',
                         'notificaciones', 'auditoria_usuarios']
    for t in tablas_requeridas:
        if t in tablas:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cur.fetchone()[0]
            ok(f"{t:35} {cnt:>5} registros")
        else:
            falta(f"Tabla no encontrada en BD: {t}")

    # Resumen de usuarios
    titulo("13. USUARIOS EN BD")
    cur.execute("SELECT id, nombre, email, tipo_usuario, activo FROM usuario ORDER BY tipo_usuario, nombre")
    for r in cur.fetchall():
        estado = "activo" if r[4] else "inactivo"
        print(f"  #{r[0]:3} [{r[3]:7}] {r[1]:25} {r[2]:35} {estado}")

    # Resumen de citas
    titulo("14. ESTADÍSTICAS DE CITAS")
    cur.execute("SELECT estado, COUNT(*) FROM citas GROUP BY estado ORDER BY estado")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  {r[0]:22} {r[1]:>3} cita(s)")
    else:
        warn("No hay citas registradas")

    # Trigger
    titulo("15. TRIGGERS EN POSTGRESQL")
    cur.execute("""
        SELECT trigger_name, event_manipulation, event_object_table
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
        ORDER BY trigger_name
    """)
    triggers = cur.fetchall()
    if triggers:
        for r in triggers:
            ok(f"{r[0]:42} {r[1]:8} ON {r[2]}")
    else:
        warn("No hay triggers — ejecuta: python scripts/rossmix_check.py --trigger")

    # Auditoría
    titulo("16. AUDITORÍA DE USUARIOS")
    try:
        cur.execute("SELECT COUNT(*) FROM auditoria_usuarios")
        cnt = cur.fetchone()[0]
        if cnt > 0:
            ok(f"{cnt} registro(s) en auditoria_usuarios")
            cur.execute("SELECT nombre, email, tipo_usuario, fecha_registro FROM auditoria_usuarios ORDER BY fecha_registro DESC LIMIT 3")
            for r in cur.fetchall():
                print(f"  {r[0]:25} {r[1]:35} {r[2]:7} {r[3].strftime('%d/%m/%Y %H:%M')}")
        else:
            warn("auditoria_usuarios está vacía — se llenará con nuevos registros")
    except Exception as e:
        warn(f"No se pudo consultar auditoria_usuarios: {e}")

    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 5 — VERIFICACIÓN DE Rossmix.sql
# ═════════════════════════════════════════════════════════════════════════════

def check_sql():
    titulo("17. ARCHIVO Rossmix.sql")
    sql_path = os.path.join(BASE, 'scripts', 'database', 'Rossmix.sql')
    if not os.path.exists(sql_path):
        falta("Rossmix.sql no encontrado"); return

    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    elementos = [
        ('LIMPIEZA COMPLETA',         'DROP de tablas y tipos'),
        ('TIPOS ENUMERADOS',          'ENUMs estado_cita_enum y metodo_pago_enum'),
        ('TABLA: USUARIO',            'Tabla usuario'),
        ('TABLA: CITAS',              'Tabla citas'),
        ('TABLA: PAGOS',              'Tabla pagos'),
        ('TABLA: NOTIFICACIONES',     'Tabla notificaciones'),
        ('TABLA: AUDITORIA_USUARIOS', 'Tabla auditoria_usuarios'),
        ('token_gestion',             'Campo token_gestion en citas'),
        ('fn_auditoria_nuevo_usuario','Función del trigger'),
        ('trg_auditoria_nuevo_usuario','Trigger de auditoría'),
        ('vista_agenda_diaria',       'Vista vista_agenda_diaria'),
        ('vista_pagos_pendientes',    'Vista vista_pagos_pendientes'),
        ('vista_nuevos_usuarios',     'Vista vista_nuevos_usuarios'),
        ('pg_notify',                 'Canal pg_notify en tiempo real'),
        ('DROP FUNCTION IF EXISTS',   'Limpieza de función al inicio'),
    ]
    for buscar, desc in elementos:
        if buscar.upper() in sql.upper() or buscar in sql:
            ok(desc)
        else:
            falta(f"Falta en Rossmix.sql: {desc}")

    lineas = sql.count('\n')
    print(f"\n  Archivo: {len(sql):,} caracteres | {lineas:,} líneas")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 6 — FIX PRECIOS (corrección de precios erróneos en BD)
# ═════════════════════════════════════════════════════════════════════════════

def fix_precios():
    titulo("FIX — CORRECCIÓN DE PRECIOS EN BD")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "app_module", os.path.join(BASE, "app.py")
        )
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        app     = m.app
        db      = m.db
        Servicio = m.Servicio
        Cita    = m.Cita
        Pago    = m.Pago
    except Exception as e:
        falta(f"No se pudo cargar app.py: {e}"); return

    PRECIO_INCORRECTO = 18001
    PRECIO_CORRECTO   = 18000

    with app.app_context():
        cambios = 0

        for s in Servicio.query.all():
            if s.precio_total == PRECIO_INCORRECTO:
                print(f"  Servicio #{s.id_servicio} precio {s.precio_total} → {PRECIO_CORRECTO}")
                s.precio_total = PRECIO_CORRECTO
                cambios += 1

        for c in Cita.query.all():
            if c.monto_total == PRECIO_INCORRECTO:
                print(f"  Cita #{c.id_cita} monto_total {c.monto_total} → {PRECIO_CORRECTO}")
                c.monto_total = PRECIO_CORRECTO
                cambios += 1
            if c.saldo_pendiente == PRECIO_INCORRECTO:
                print(f"  Cita #{c.id_cita} saldo_pendiente → {PRECIO_CORRECTO}")
                c.saldo_pendiente = PRECIO_CORRECTO
                cambios += 1

        for p in Pago.query.all():
            if p.monto == PRECIO_INCORRECTO:
                print(f"  Pago #{p.id_pago} monto {p.monto} → {PRECIO_CORRECTO}")
                p.monto = PRECIO_CORRECTO
                cambios += 1

        if cambios > 0:
            db.session.commit()
            ok(f"{cambios} precio(s) corregido(s) y guardados en BD")
        else:
            ok("No hay precios incorrectos (18001) en la BD")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 7 — INSTALAR TRIGGER DE AUDITORÍA
# ═════════════════════════════════════════════════════════════════════════════

def instalar_trigger():
    titulo("INSTALAR — TRIGGER DE AUDITORÍA EN POSTGRESQL")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "app_module", os.path.join(BASE, "app.py")
        )
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        app = m.app
        db  = m.db
    except Exception as e:
        falta(f"No se pudo cargar app.py: {e}"); return

    SQL_AUDITORIA = """
    CREATE TABLE IF NOT EXISTS auditoria_usuarios (
        id             SERIAL PRIMARY KEY,
        id_usuario     INTEGER NOT NULL,
        nombre         VARCHAR(100),
        email          VARCHAR(120),
        telefono       VARCHAR(20),
        tipo_usuario   VARCHAR(20),
        fecha_registro TIMESTAMP DEFAULT NOW(),
        accion         VARCHAR(10) DEFAULT 'INSERT'
    );
    """
    SQL_FUNCION = """
    CREATE OR REPLACE FUNCTION fn_auditoria_nuevo_usuario()
    RETURNS TRIGGER AS $$
    BEGIN
        INSERT INTO auditoria_usuarios (
            id_usuario, nombre, email, telefono, tipo_usuario, fecha_registro, accion
        ) VALUES (
            NEW.id, NEW.nombre, NEW.email, NEW.telefono,
            NEW.tipo_usuario, NEW.fecha_registro, 'INSERT'
        );
        PERFORM pg_notify(
            'nuevo_usuario',
            json_build_object(
                'id',           NEW.id,
                'nombre',       NEW.nombre,
                'email',        NEW.email,
                'tipo_usuario', NEW.tipo_usuario,
                'fecha',        to_char(NEW.fecha_registro, 'DD/MM/YYYY HH24:MI:SS')
            )::text
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    SQL_TRIGGER = """
    DROP TRIGGER IF EXISTS trg_auditoria_nuevo_usuario ON usuario;
    CREATE TRIGGER trg_auditoria_nuevo_usuario
        AFTER INSERT ON usuario
        FOR EACH ROW
        EXECUTE FUNCTION fn_auditoria_nuevo_usuario();
    """
    SQL_VISTA = """
    CREATE OR REPLACE VIEW vista_nuevos_usuarios AS
        SELECT id, id_usuario, nombre, email, telefono,
               tipo_usuario, fecha_registro, accion
        FROM auditoria_usuarios
        ORDER BY fecha_registro DESC;
    """

    with app.app_context():
        for nombre_sql, sql in [
            ("Tabla auditoria_usuarios", SQL_AUDITORIA),
            ("Función fn_auditoria_nuevo_usuario", SQL_FUNCION),
            ("Trigger trg_auditoria_nuevo_usuario", SQL_TRIGGER),
            ("Vista vista_nuevos_usuarios", SQL_VISTA),
        ]:
            try:
                db.session.execute(db.text(sql))
                db.session.commit()
                ok(nombre_sql)
            except Exception as e:
                falta(f"Error en {nombre_sql}: {e}")
                db.session.rollback()


# ═════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    args = sys.argv[1:]

    print()
    print("=" * 64)
    print("   ROSSMIX -- VERIFICACION COMPLETA DEL PROYECTO")
    print("=" * 64)

    if '--fix' in args:
        fix_precios()

    elif '--trigger' in args:
        instalar_trigger()

    elif '--bd' in args:
        check_bd()

    elif '--code' in args:
        check_dependencias()
        check_codigo()
        check_seguridad()
        check_sql()

    else:
        # Ejecutar todo
        check_dependencias()
        check_codigo()
        check_seguridad()
        check_bd()
        check_sql()

    resumen_final()

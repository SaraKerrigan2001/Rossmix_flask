"""
ROSSMIX — SCRIPT MAESTRO UNIFICADO
═══════════════════════════════════════════════════════════════

Consolida en un solo archivo:
  ✔ rossmix_check.py   — verificación completa del proyecto
  ✔ fix_token_gestion.py — migración de columnas faltantes en BD
  ✔ Rossmix.sql         — inicialización / re-creación de la BD

USO:
  python scripts/rossmix_check.py              → verificación completa
  python scripts/rossmix_check.py --bd         → solo base de datos
  python scripts/rossmix_check.py --code       → solo código / archivos
  python scripts/rossmix_check.py --sql        → verificar Rossmix.sql
  python scripts/rossmix_check.py --migrate    → agregar columnas faltantes (token_gestion, etc.)
  python scripts/rossmix_check.py --init-db    → ejecutar Rossmix.sql (recrea toda la BD)
  python scripts/rossmix_check.py --trigger    → instalar trigger de auditoría
  python scripts/rossmix_check.py --fix        → corregir precios incorrectos en BD
"""

import os, ast, re, sys, subprocess

# ── Rutas base ────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_FILE = os.path.join(BASE, 'scripts', 'database', 'Rossmix.sql')
sys.path.insert(0, BASE)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE, '.env'))
except ImportError:
    pass

# ── Contadores globales ───────────────────────────────────────────────────────
ERRORES  = []
WARNINGS = []

def titulo(texto):
    linea = '═' * 64
    print(f"\n{linea}\n  {texto}\n{linea}")

def ok(msg):    print(f"  ✔  {msg}")
def falta(msg): print(f"  ✘  {msg}"); ERRORES.append(msg)
def warn(msg):  print(f"  ⚠  {msg}"); WARNINGS.append(msg)

def resumen_final():
    print(f"\n{'═'*64}")
    print(f"  RESULTADO FINAL")
    print(f"{'═'*64}")
    if not ERRORES and not WARNINGS:
        print("  ✔  TODO CORRECTO — el proyecto está en perfecto estado.")
    else:
        if ERRORES:
            print(f"\n  Errores ({len(ERRORES)}):")
            for e in ERRORES: print(f"    ✘  {e}")
        if WARNINGS:
            print(f"\n  Avisos ({len(WARNINGS)}):")
            for w in WARNINGS: print(f"    ⚠  {w}")
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
    titulo("2. SINTAXIS DE app.py")
    app_path = os.path.join(BASE, 'app.py')
    if not os.path.exists(app_path):
        warn("app.py no encontrado — proyecto usa blueprints (app/__init__.py)")
        _check_blueprints()
        return

    with open(app_path, 'r', encoding='utf-8') as f:
        src = f.read()

    try:
        ast.parse(src)
        ok("Sintaxis correcta")
    except SyntaxError as e:
        falta(f"Error de sintaxis en línea {e.lineno}: {e.msg}"); return

    titulo("3. RUTAS REGISTRADAS en app.py")
    rutas = re.findall(r"@app\.route\('([^']+)'", src)
    ok(f"{len(rutas)} rutas encontradas")

    titulo("4. FUNCIONES DUPLICADAS")
    funcs = re.findall(r'^def (\w+)\(', src, re.MULTILINE)
    dups  = {k: v for k, v in {f: funcs.count(f) for f in funcs}.items() if v > 1}
    if dups:
        for k, v in dups.items(): falta(f"Función duplicada: {k} ({v} veces)")
    else:
        ok("Ninguna función duplicada")

    _check_templates()
    _check_imagenes()


def _check_blueprints():
    """Verifica la arquitectura de blueprints cuando no hay app.py monolítico."""
    titulo("3. ARQUITECTURA BLUEPRINTS")
    archivos = [
        'app/__init__.py',
        'app/extensions.py',
        'app/config.py',
        'app/models/__init__.py',
        'app/models/usuario.py',
        'app/models/cita.py',
        'app/models/empleado.py',
        'app/models/servicio.py',
        'app/models/horario.py',
        'app/models/pago.py',
        'app/models/notificacion.py',
        'app/views/__init__.py',
        'app/views/auth.py',
        'app/views/citas.py',
        'app/views/cliente.py',
        'app/views/especialista.py',
        'app/views/admin/__init__.py',
        'app/views/admin/citas.py',
        'app/views/admin/empleados.py',
        'app/views/admin/servicios.py',
        'app/views/admin/clientes.py',
        'app/views/admin/horarios.py',
        'app/views/admin/pagos.py',
        'app/views/admin/especialistas.py',
        'app/views/admin/dashboard.py',
        'app/views/admin/exportar.py',
        'app/utils/decorators.py',
        'app/utils/helpers.py',
    ]
    ok_c = fail_c = 0
    for f in archivos:
        path = os.path.join(BASE, f)
        if os.path.exists(path):
            ok(f); ok_c += 1
        else:
            falta(f"Faltante: {f}"); fail_c += 1
    print(f"\n  Total: {ok_c} OK, {fail_c} faltantes")
    _check_templates()
    _check_imagenes()

def _check_templates():
    titulo("5. TEMPLATES HTML")
    templates = [
        'base.html', 'index.html', 'login.html', 'registro.html',
        'dashboard_admin.html', 'dashboard_cliente.html', 'notificaciones.html',
        'citas/paso1_servicio.html', 'citas/paso2_empleado.html',
        'citas/paso3_fecha_hora.html', 'citas/paso4_confirmacion.html',
        'citas/confirmada.html', 'citas/mis_citas.html',
        'citas/cliente_pagos_form.html',
        'especialista/dashboard.html', 'especialista/citas_disponibles.html',
        'especialista/mis_citas.html',
        'admin/citas.html', 'admin/empleados.html', 'admin/servicios.html',
        'admin/clientes.html', 'admin/horarios.html',
        'admin/pagos.html', 'admin/pagos_form.html',
        'admin/especialistas.html', 'admin/distribucion_citas.html',
    ]
    tpl_base = os.path.join(BASE, 'app', 'templates')
    ok_t = fail_t = 0
    for t in templates:
        if os.path.exists(os.path.join(tpl_base, t)):
            ok(t); ok_t += 1
        else:
            falta(f"Template faltante: {t}"); fail_t += 1
    print(f"\n  Total: {ok_t} OK, {fail_t} faltantes")

def _check_imagenes():
    titulo("6. IMÁGENES ESTÁTICAS")
    img_dir = os.path.join(BASE, 'app', 'static', 'images')
    if not os.path.exists(img_dir):
        warn("Directorio images/ no encontrado"); return
    archivos = []
    for root, _, files in os.walk(img_dir):
        for f in files:
            archivos.append(os.path.join(root, f))
    ok_i = fail_i = 0
    for path in sorted(archivos):
        with open(path, 'rb') as fp: h = fp.read(4)
        if h[:2] == b'\xff\xd8':   tipo = 'JPEG'
        elif h[1:4] == b'PNG':     tipo = 'PNG'
        elif h[:3] == b'GIF':      tipo = 'GIF'
        elif h[:4] == b'RIFF':     tipo = 'WEBP'
        else:                      tipo = 'INVAL'
        size = round(os.path.getsize(path)/1024, 1)
        nombre = os.path.relpath(path, img_dir)
        if tipo != 'INVAL':
            ok(f"{tipo:<5} {size:>7} KB  {nombre}"); ok_i += 1
        else:
            warn(f"Archivo no es imagen válida: {nombre}"); fail_i += 1
    print(f"\n  Total: {ok_i} OK, {fail_i} inválidas")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 3 — SEGURIDAD
# ═════════════════════════════════════════════════════════════════════════════

def check_seguridad():
    titulo("7. SEGURIDAD — CREDENCIALES Y GIT")
    archivos_a_revisar = []
    for root, _, files in os.walk(os.path.join(BASE, 'app')):
        for f in files:
            if f.endswith('.py'):
                archivos_a_revisar.append(os.path.join(root, f))
    app_py = os.path.join(BASE, 'app.py')
    if os.path.exists(app_py):
        archivos_a_revisar.append(app_py)

    patrones_peligrosos = [
        ('postgres:1234',           'Contraseña BD hardcodeada'),
        ("SECRET_KEY = 'tu_clave",  'SECRET_KEY hardcodeada'),
        ('password="1234"',         'password=1234 hardcodeada'),
        ("password='1234'",         'password=1234 hardcodeada'),
    ]
    alguno = False
    for ruta in archivos_a_revisar:
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        for patron, desc in patrones_peligrosos:
            if patron in contenido:
                rel = os.path.relpath(ruta, BASE)
                falta(f"{desc} en {rel}"); alguno = True
    if not alguno:
        ok("Sin credenciales hardcodeadas")

    r1 = subprocess.run(['git','ls-files','.env'], capture_output=True, text=True, cwd=BASE)
    if r1.stdout.strip(): falta(".env está trackeado en Git")
    else:                 ok(".env NO está en Git")

    r2 = subprocess.run(['git','ls-files','.env.example'], capture_output=True, text=True, cwd=BASE)
    if r2.stdout.strip(): ok(".env.example sí está en Git")
    else:                 warn(".env.example no está en Git — recomendable incluirlo")

    titulo("8. VARIABLES DE ENTORNO")
    vars_req = ['SECRET_KEY','DB_USER','DB_PASSWORD','DB_HOST','DB_NAME',
                'ADMIN_EMAIL','ADMIN_PASSWORD']
    for v in vars_req:
        val = os.environ.get(v)
        if val:
            masked = '***' if ('PASSWORD' in v or 'KEY' in v) else val
            ok(f"{v} = {masked}")
        else:
            warn(f"Variable no definida: {v}")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 4 — BASE DE DATOS
# ═════════════════════════════════════════════════════════════════════════════

def _get_conn():
    import psycopg
    return psycopg.connect(
        host    =os.environ.get('DB_HOST',     'localhost'),
        port    =os.environ.get('DB_PORT',     '5432'),
        dbname  =os.environ.get('DB_NAME',     'Rossmix'),
        user    =os.environ.get('DB_USER',     'postgres'),
        password=os.environ.get('DB_PASSWORD', ''),
    )

def check_bd():
    titulo("9. CONEXIÓN A POSTGRESQL")
    try:
        import psycopg
    except ImportError:
        falta("psycopg no instalado"); return
    try:
        conn = _get_conn()
        ok("Conexión exitosa a PostgreSQL")
    except Exception as e:
        falta(f"No se pudo conectar: {e}"); return

    cur = conn.cursor()

    titulo("10. TABLAS Y REGISTROS")
    tablas_req = ['usuario','servicios','empleados','empleado_servicios',
                  'horarios_empleados','citas','pagos','notificaciones','auditoria_usuarios']
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    tablas_bd = [r[0] for r in cur.fetchall()]
    for t in tablas_req:
        if t in tablas_bd:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cur.fetchone()[0]
            ok(f"{t:35} {cnt:>5} registros")
        else:
            falta(f"Tabla no encontrada: {t}")

    titulo("11. COLUMNAS CLAVE DE CITAS")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='citas'")
    cols_citas = [r[0] for r in cur.fetchall()]
    for col in ['token_gestion','codigo_reserva','estado','monto_abono',
                'saldo_pendiente','notas','fecha_hora_inicio','fecha_hora_fin']:
        if col in cols_citas: ok(f"citas.{col}")
        else:                 falta(f"citas.{col} — faltante (ejecuta --migrate)")

    titulo("12. COLUMNAS CLAVE DE USUARIO")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='usuario'")
    cols_usu = [r[0] for r in cur.fetchall()]
    for col in ['id','nombre','email','telefono','password','tipo_usuario',
                'fecha_registro','activo','id_empleado']:
        if col in cols_usu: ok(f"usuario.{col}")
        else:               falta(f"usuario.{col} — faltante (ejecuta --migrate)")

    titulo("13. USUARIOS EN BD")
    cur.execute("SELECT id, nombre, email, tipo_usuario, activo FROM usuario ORDER BY tipo_usuario, nombre")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            estado = "activo" if r[4] else "inactivo"
            print(f"  #{r[0]:3} [{r[3]:12}] {r[1]:25} {r[2]:35} {estado}")
    else:
        warn("No hay usuarios en la BD")

    titulo("14. ESTADÍSTICAS DE CITAS")
    cur.execute("SELECT estado, COUNT(*) FROM citas GROUP BY estado ORDER BY estado")
    rows = cur.fetchall()
    if rows:
        for r in rows: print(f"  {r[0]:22} {r[1]:>3} cita(s)")
    else:
        warn("No hay citas registradas")

    titulo("15. TRIGGERS EN POSTGRESQL")
    cur.execute("""SELECT trigger_name, event_manipulation, event_object_table
                   FROM information_schema.triggers WHERE trigger_schema='public'
                   ORDER BY trigger_name""")
    triggers = cur.fetchall()
    if triggers:
        for r in triggers: ok(f"{r[0]:42} {r[1]:8} ON {r[2]}")
    else:
        warn("Sin triggers — ejecuta --trigger para instalarlos")

    titulo("16. AUDITORÍA DE USUARIOS")
    try:
        cur.execute("SELECT COUNT(*) FROM auditoria_usuarios")
        cnt = cur.fetchone()[0]
        if cnt > 0:
            ok(f"{cnt} registro(s) en auditoria_usuarios")
            cur.execute("SELECT nombre, email, tipo_usuario, fecha_registro "
                        "FROM auditoria_usuarios ORDER BY fecha_registro DESC LIMIT 3")
            for r in cur.fetchall():
                print(f"  {r[0]:25} {r[1]:35} {r[2]:12} {r[3].strftime('%d/%m/%Y %H:%M')}")
        else:
            warn("auditoria_usuarios vacía — ejecuta: python scripts/rossmix_check.py --backfill")
    except Exception as e:
        warn(f"No se pudo consultar auditoria_usuarios: {e}")

    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 5 — VERIFICAR Rossmix.sql  (antes era check_sql en rossmix_check.py)
# ═════════════════════════════════════════════════════════════════════════════

def check_sql():
    titulo("17. ARCHIVO Rossmix.sql")
    if not os.path.exists(SQL_FILE):
        falta(f"Rossmix.sql no encontrado en: {SQL_FILE}"); return

    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()

    elementos = [
        ('LIMPIEZA COMPLETA',          'Bloque de limpieza / DROP'),
        ('TIPOS ENUMERADOS',           'ENUMs estado_cita_enum y metodo_pago_enum'),
        ('TABLA: USUARIO',             'Tabla usuario'),
        ('TABLA: CITAS',               'Tabla citas'),
        ('TABLA: PAGOS',               'Tabla pagos'),
        ('TABLA: NOTIFICACIONES',      'Tabla notificaciones'),
        ('TABLA: AUDITORIA_USUARIOS',  'Tabla auditoria_usuarios'),
        ('token_gestion',              'Campo token_gestion en citas'),
        ('fn_auditoria_nuevo_usuario', 'Función del trigger'),
        ('trg_auditoria_nuevo_usuario','Trigger de auditoría'),
        ('vista_agenda_diaria',        'Vista vista_agenda_diaria'),
        ('vista_pagos_pendientes',     'Vista vista_pagos_pendientes'),
        ('vista_nuevos_usuarios',      'Vista vista_nuevos_usuarios'),
        ('pg_notify',                  'Canal pg_notify en tiempo real'),
        ('DROP FUNCTION IF EXISTS',    'Limpieza de función al inicio'),
    ]
    for buscar, desc in elementos:
        if buscar.upper() in sql.upper() or buscar in sql:
            ok(desc)
        else:
            falta(f"Falta en Rossmix.sql: {desc}")

    lineas = sql.count('\n')
    print(f"\n  Archivo: {len(sql):,} caracteres | {lineas:,} líneas")
    ok(f"Rossmix.sql en: scripts/database/Rossmix.sql")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 6 — MIGRATE: agregar columnas faltantes
#            (antes era fix_token_gestion.py — ejecutar una sola vez)
# ═════════════════════════════════════════════════════════════════════════════

def migrate_columnas():
    """
    Agrega columnas faltantes a la BD en PostgreSQL.
    Seguro de ejecutar varias veces (idempotente).
    """
    titulo("MIGRATE — COLUMNAS FALTANTES EN BD")
    try:
        conn = _get_conn()
    except Exception as e:
        falta(f"No se pudo conectar: {e}"); return

    cur = conn.cursor()

    # Lista de (tabla, columna, SQL ALTER TABLE)
    migraciones = [
        ('citas',   'token_gestion',
         "ALTER TABLE citas ADD COLUMN token_gestion VARCHAR(32) UNIQUE"),
        ('usuario', 'id_empleado',
         "ALTER TABLE usuario ADD COLUMN id_empleado INTEGER "
         "REFERENCES empleados(id_empleado) ON DELETE SET NULL"),
    ]

    for tabla, col, sql_alter in migraciones:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name=%s AND column_name=%s",
            (tabla, col)
        )
        if cur.fetchone():
            ok(f"{tabla}.{col} ya existe — sin cambios")
        else:
            try:
                cur.execute(sql_alter)
                conn.commit()
                ok(f"{tabla}.{col} — columna agregada ✔")
            except Exception as e:
                conn.rollback()
                falta(f"Error al agregar {tabla}.{col}: {e}")

    # Estado final de la tabla citas
    titulo("Estado actual — columnas de 'citas'")
    cur.execute(
        "SELECT column_name, data_type, character_maximum_length "
        "FROM information_schema.columns "
        "WHERE table_name='citas' ORDER BY ordinal_position"
    )
    for r in cur.fetchall():
        largo = f"({r[2]})" if r[2] else ''
        print(f"  {r[0]:30} {r[1]}{largo}")

    # Estado final de la tabla usuario
    titulo("Estado actual — columnas de 'usuario'")
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='usuario' ORDER BY ordinal_position"
    )
    for r in cur.fetchall():
        print(f"  {r[0]:30} {r[1]}")

    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 7 — INIT-DB: ejecutar Rossmix.sql completo
# ═════════════════════════════════════════════════════════════════════════════

def init_db():
    """
    Ejecuta Rossmix.sql directamente sobre PostgreSQL.
    ¡ATENCIÓN! Este comando BORRA y RECREA todas las tablas.
    """
    titulo("INIT-DB — EJECUTAR Rossmix.sql")

    if not os.path.exists(SQL_FILE):
        falta(f"Rossmix.sql no encontrado: {SQL_FILE}"); return

    print(f"\n  ⚠  ATENCIÓN: Este comando eliminará y recreará TODAS las tablas.")
    print(f"  Archivo: {SQL_FILE}")
    confirmar = input("\n  ¿Confirmar? Escribe 'SI' para continuar: ").strip()
    if confirmar.upper() != 'SI':
        print("  Operación cancelada."); return

    try:
        conn = _get_conn()
        conn.autocommit = True
        cur = conn.cursor()
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql = f.read()
        cur.execute(sql)
        ok("Rossmix.sql ejecutado exitosamente")
        conn.close()
    except Exception as e:
        falta(f"Error al ejecutar Rossmix.sql: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 8 — TRIGGER DE AUDITORÍA
# ═════════════════════════════════════════════════════════════════════════════

def instalar_trigger():
    titulo("TRIGGER — AUDITORÍA DE NUEVOS USUARIOS")
    try:
        conn = _get_conn()
    except Exception as e:
        falta(f"No se pudo conectar: {e}"); return

    cur = conn.cursor()

    sqls = [
        ("Tabla auditoria_usuarios", """
            CREATE TABLE IF NOT EXISTS auditoria_usuarios (
                id             SERIAL PRIMARY KEY,
                id_usuario     INTEGER NOT NULL,
                nombre         VARCHAR(100),
                email          VARCHAR(120),
                telefono       VARCHAR(20),
                tipo_usuario   VARCHAR(20),
                fecha_registro TIMESTAMP DEFAULT NOW(),
                accion         VARCHAR(10) DEFAULT 'INSERT',
                ip_address     VARCHAR(45)
            )
        """),
        ("Función fn_auditoria_nuevo_usuario", """
            CREATE OR REPLACE FUNCTION fn_auditoria_nuevo_usuario()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO auditoria_usuarios
                    (id_usuario, nombre, email, telefono, tipo_usuario, fecha_registro, accion)
                VALUES
                    (NEW.id, NEW.nombre, NEW.email, NEW.telefono,
                     NEW.tipo_usuario, NEW.fecha_registro, 'INSERT');
                PERFORM pg_notify('nuevo_usuario',
                    json_build_object(
                        'id', NEW.id, 'nombre', NEW.nombre,
                        'email', NEW.email, 'tipo_usuario', NEW.tipo_usuario,
                        'fecha', to_char(NEW.fecha_registro, 'DD/MM/YYYY HH24:MI:SS')
                    )::text);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """),
        ("Trigger trg_auditoria_nuevo_usuario", """
            DROP TRIGGER IF EXISTS trg_auditoria_nuevo_usuario ON usuario;
            CREATE TRIGGER trg_auditoria_nuevo_usuario
                AFTER INSERT ON usuario
                FOR EACH ROW EXECUTE FUNCTION fn_auditoria_nuevo_usuario()
        """),
        ("Vista vista_nuevos_usuarios", """
            CREATE OR REPLACE VIEW vista_nuevos_usuarios AS
                SELECT id, id_usuario, nombre, email, telefono,
                       tipo_usuario, fecha_registro, accion
                FROM auditoria_usuarios ORDER BY fecha_registro DESC
        """),
    ]

    for nombre_sql, sql in sqls:
        try:
            cur.execute(sql)
            conn.commit()
            ok(nombre_sql)
        except Exception as e:
            conn.rollback()
            falta(f"Error en {nombre_sql}: {e}")

    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 9 — FIX PRECIOS (corrección de valores 18001 → 18000)
# ═════════════════════════════════════════════════════════════════════════════

def fix_precios():
    titulo("FIX — CORRECCIÓN DE PRECIOS INCORRECTOS EN BD")
    INCORRECTO = 18001
    CORRECTO   = 18000

    try:
        conn = _get_conn()
    except Exception as e:
        falta(f"No se pudo conectar: {e}"); return

    cur = conn.cursor()
    cambios = 0

    for tabla, col in [('servicios','precio_total'), ('citas','monto_total'),
                       ('citas','saldo_pendiente'), ('pagos','monto')]:
        cur.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {col} = %s", (INCORRECTO,))
        cnt = cur.fetchone()[0]
        if cnt > 0:
            cur.execute(f"UPDATE {tabla} SET {col} = %s WHERE {col} = %s", (CORRECTO, INCORRECTO))
            ok(f"{tabla}.{col}: {cnt} registro(s) corregido(s)")
            cambios += cnt
        else:
            ok(f"{tabla}.{col}: sin valores incorrectos")

    if cambios > 0:
        conn.commit()
        ok(f"Total: {cambios} precio(s) corregido(s) y guardados")
    else:
        ok("No hay precios incorrectos (18001) en la BD")

    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# MÓDULO 10 — BACKFILL: poblar auditoria_usuarios con registros existentes
# ═════════════════════════════════════════════════════════════════════════════

def backfill_auditoria():
    """
    Inserta en auditoria_usuarios todos los usuarios que aún no aparecen.
    Idempotente: no duplica si se ejecuta varias veces.
    También prueba el trigger con un INSERT temporal.
    """
    titulo("BACKFILL — AUDITORÍA DE USUARIOS EXISTENTES")
    try:
        conn = _get_conn()
    except Exception as e:
        falta(f"No se pudo conectar: {e}"); return

    cur = conn.cursor()

    # Importar usuarios que no están en auditoría
    cur.execute("""
        INSERT INTO auditoria_usuarios
            (id_usuario, nombre, email, telefono, tipo_usuario, fecha_registro, accion)
        SELECT u.id, u.nombre, u.email, u.telefono,
               u.tipo_usuario, u.fecha_registro, 'BACKFILL'
        FROM usuario u
        WHERE NOT EXISTS (
            SELECT 1 FROM auditoria_usuarios a WHERE a.id_usuario = u.id
        )
        ORDER BY u.id
    """)
    importados = cur.rowcount
    conn.commit()

    if importados > 0:
        ok(f"{importados} usuario(s) importados a auditoria_usuarios")
    else:
        ok("Todos los usuarios ya estaban en auditoría — sin cambios")

    # Mostrar contenido actual
    titulo("Contenido de auditoria_usuarios")
    cur.execute("""
        SELECT id_usuario, nombre, email, tipo_usuario, accion, fecha_registro
        FROM auditoria_usuarios ORDER BY id_usuario
    """)
    rows = cur.fetchall()
    ok(f"Total: {len(rows)} registro(s)")
    for r in rows:
        fecha = r[5].strftime('%d/%m/%Y %H:%M') if r[5] else '—'
        print(f"  #{r[0]:3} [{r[3]:12}] {r[1]:25} {r[4]:10} {fecha}")

    # Verificar trigger con usuario temporal
    titulo("Prueba del trigger")
    try:
        cur.execute("""
            INSERT INTO usuario (nombre, email, telefono, password, tipo_usuario)
            VALUES ('TEST_TRIGGER', 'test_trigger_tmp@rossmix.com',
                    '0000000000', 'hash_tmp', 'cliente')
            RETURNING id
        """)
        new_id = cur.fetchone()[0]
        conn.commit()

        cur.execute("SELECT accion FROM auditoria_usuarios WHERE id_usuario = %s", (new_id,))
        audit = cur.fetchone()

        if audit:
            ok(f"Trigger OK — usuario #{new_id} capturado automáticamente (acción: '{audit[0]}')")
        else:
            falta("Trigger NO funcionó — reinstalar con: python scripts/rossmix_check.py --trigger")

        # Limpiar usuario temporal
        cur.execute("DELETE FROM auditoria_usuarios WHERE id_usuario = %s", (new_id,))
        cur.execute("DELETE FROM usuario WHERE id = %s", (new_id,))
        conn.commit()
        ok(f"Usuario temporal #{new_id} eliminado")
    except Exception as e:
        conn.rollback()
        falta(f"Error en prueba del trigger: {e}")

    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═════════════════════════════════════════════════════════════════════════════

AYUDA = """
ROSSMIX — Script Maestro Unificado
═══════════════════════════════════
  (sin flags)    Verificación completa del proyecto
  --bd           Solo base de datos
  --code         Solo código, archivos y templates
  --sql          Verificar Rossmix.sql
  --migrate      Agregar columnas faltantes (token_gestion, id_empleado, etc.)
  --init-db      Ejecutar Rossmix.sql — RECREA toda la BD ⚠
  --trigger      Instalar trigger de auditoría en PostgreSQL
  --backfill     Poblar auditoria_usuarios con usuarios existentes + probar trigger
  --fix          Corregir precios incorrectos (18001→18000) en BD
  --help         Mostrar esta ayuda
"""

if __name__ == '__main__':
    args = sys.argv[1:]

    if '--help' in args:
        print(AYUDA); sys.exit(0)

    print()
    print("═" * 64)
    print("   ROSSMIX — SCRIPT MAESTRO UNIFICADO")
    print("   rossmix_check  ·  fix_token_gestion  ·  Rossmix.sql")
    print("═" * 64)

    if '--migrate' in args:
        migrate_columnas()

    elif '--init-db' in args:
        init_db()

    elif '--trigger' in args:
        instalar_trigger()

    elif '--backfill' in args:
        backfill_auditoria()

    elif '--fix' in args:
        fix_precios()

    elif '--bd' in args:
        check_bd()

    elif '--code' in args:
        check_dependencias()
        check_codigo()
        check_seguridad()

    elif '--sql' in args:
        check_sql()

    else:
        # Verificación completa
        check_dependencias()
        check_codigo()
        check_seguridad()
        check_bd()
        check_sql()

    resumen_final()

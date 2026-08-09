"""
Pobla la tabla usuario con admin + clientes de prueba.
Ejecutar UNA SOLA VEZ después de correr rossmix_definitivo.sql

Las credenciales (conexión a la BD y contraseñas de los usuarios de
prueba) se leen desde variables de entorno / archivo ".env" en lugar de
estar escritas en este archivo. Ver ".env.example" para la lista de
variables disponibles.

Variables de entorno usadas por este script:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  SEED_ADMIN_PASSWORD       (contraseña para los usuarios admin de prueba)
  SEED_CLIENTE_PASSWORD     (contraseña para los usuarios cliente de prueba)
"""
import os
import sys

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import psycopg

load_dotenv()

DB = dict(
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', '5432'),
    dbname=os.environ.get('DB_NAME', 'Rossmix'),
    user=os.environ.get('DB_USER', 'postgres'),
    password=os.environ.get('DB_PASSWORD'),
)

if not DB['password']:
    sys.exit(
        'Error: falta la variable de entorno DB_PASSWORD.\n'
        'Define las variables de conexión en tu archivo .env '
        '(ver .env.example) antes de ejecutar este script.'
    )

# Contraseñas de los usuarios de prueba: también configurables por entorno,
# con un valor por defecto solo para no romper el flujo de desarrollo local.
ADMIN_PWD   = os.environ.get('SEED_ADMIN_PASSWORD',   'admin123')
CLIENTE_PWD = os.environ.get('SEED_CLIENTE_PASSWORD', 'cliente123')

usuarios = [
    # (nombre,               email,                         telefono,     password,     tipo)
    ("Administrador",        "admin@rossmix.com",           "3000000000", ADMIN_PWD,    "admin"),
    ("María González",       "maria@rossmix.com",           "3001234567", ADMIN_PWD,    "admin"),
    ("Andrea Vargas",        "andrea.vargas@email.com",     "3100000001", CLIENTE_PWD,  "cliente"),
    ("Patricia Silva",       "patricia.silva@email.com",    "3100000002", CLIENTE_PWD,  "cliente"),
    ("Diana Gutierrez",      "diana.gutierrez@email.com",   "3100000003", CLIENTE_PWD,  "cliente"),
    ("Juliana Rojas",        "juliana.rojas@email.com",     "3100000004", CLIENTE_PWD,  "cliente"),
    ("Catalina Mendoza",     "catalina.mendoza@email.com",  "3100000005", CLIENTE_PWD,  "cliente"),
    ("Valentina Perez",      "valentina.perez@email.com",   "3100000006", CLIENTE_PWD,  "cliente"),
    ("Isabella Garcia",      "isabella.garcia@email.com",   "3100000007", CLIENTE_PWD,  "cliente"),
    ("Laura Martinez",       "laura.martinez@email.com",    "3100000008", CLIENTE_PWD,  "cliente"),
    ("Evelit Collante",      "evelit@gmail.co",             "3100000009", CLIENTE_PWD,  "cliente"),
    ("Carlos Prieto",        "carlos@gmail.com",            "3456789123", CLIENTE_PWD,  "cliente"),
]

conn = psycopg.connect(**DB)
cur  = conn.cursor()

print("=" * 58)
print("CREANDO USUARIOS — ROSSMIX")
print("=" * 58)

ok = 0
for nombre, email, tel, pwd, tipo in usuarios:
    try:
        cur.execute(
            "INSERT INTO usuario (nombre, email, telefono, password, tipo_usuario) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
            (nombre, email, tel, generate_password_hash(pwd), tipo)
        )
        tag = "ADMIN  " if tipo == "admin" else "cliente"
        print(f"  [{tag}] {nombre:25s} {email}")
        ok += 1
    except Exception as e:
        print(f"  ERROR {email}: {e}")

conn.commit()

# Verificación final
cur.execute("SELECT tipo_usuario, COUNT(*) FROM usuario GROUP BY tipo_usuario")
print(f"\nResultado en BD:")
for row in cur.fetchall():
    print(f"  {row[0]:8s}: {row[1]} usuario(s)")

cur.close()
conn.close()
print(f"\n{ok} usuarios procesados correctamente.")
print("\nCredenciales usadas (definidas por variables de entorno):")
print(f"  Admin:   admin@rossmix.com        /  (SEED_ADMIN_PASSWORD)")
print(f"  Cliente: andrea.vargas@email.com  /  (SEED_CLIENTE_PASSWORD)")

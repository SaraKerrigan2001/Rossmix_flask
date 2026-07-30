"""
Pobla la tabla usuario con admin + clientes de prueba
Ejecutar UNA SOLA VEZ después de correr rossmix_definitivo.sql
"""
from werkzeug.security import generate_password_hash
import psycopg


DB = dict(host="localhost", port=5432, dbname="Rossmix", user="postgres", password="1234")

usuarios = [
    # (nombre,               email,                         telefono,     password,     tipo)
    ("Administrador",        "admin@rossmix.com",           "3000000000", "admin123",   "admin"),
    ("María González",       "maria@rossmix.com",           "3001234567", "maria123",   "admin"),
    ("Andrea Vargas",        "andrea.vargas@email.com",     "3100000001", "cliente123", "cliente"),
    ("Patricia Silva",       "patricia.silva@email.com",    "3100000002", "cliente123", "cliente"),
    ("Diana Gutierrez",      "diana.gutierrez@email.com",   "3100000003", "cliente123", "cliente"),
    ("Juliana Rojas",        "juliana.rojas@email.com",     "3100000004", "cliente123", "cliente"),
    ("Catalina Mendoza",     "catalina.mendoza@email.com",  "3100000005", "cliente123", "cliente"),
    ("Valentina Perez",      "valentina.perez@email.com",   "3100000006", "cliente123", "cliente"),
    ("Isabella Garcia",      "isabella.garcia@email.com",   "3100000007", "cliente123", "cliente"),
    ("Laura Martinez",       "laura.martinez@email.com",    "3100000008", "cliente123", "cliente"),
    ("Evelit Collante",      "evelit@gmail.co",             "3100000009", "trululu",    "cliente"),
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
print("\nCredenciales:")
print("  Admin:   admin@rossmix.com        /  admin123")
print("  Cliente: andrea.vargas@email.com  /  cliente123")

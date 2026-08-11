"""Inserta todos los usuarios de prueba directamente via psycopg."""
import os
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError: pass

import psycopg
from werkzeug.security import generate_password_hash

ADMIN_PWD   = os.environ.get('SEED_ADMIN_PASSWORD',  'admin123')
CLIENTE_PWD = os.environ.get('SEED_CLIENTE_PASSWORD', 'cliente123')

USUARIOS = [
    ('Administrador',    'admin@rossmix.com',         '3000000000', 'admin',   ADMIN_PWD),
    ('María González',   'maria@rossmix.com',         '3001000000', 'admin',   ADMIN_PWD),
    ('Andrea Vargas',    'andrea.vargas@email.com',    '3001000001', 'cliente', CLIENTE_PWD),
    ('Patricia Silva',   'patricia.silva@email.com',   '3001000002', 'cliente', CLIENTE_PWD),
    ('Diana Gutierrez',  'diana.gutierrez@email.com',  '3001000003', 'cliente', CLIENTE_PWD),
    ('Juliana Rojas',    'juliana.rojas@email.com',    '3001000004', 'cliente', CLIENTE_PWD),
    ('Catalina Mendoza', 'catalina.mendoza@email.com', '3001000005', 'cliente', CLIENTE_PWD),
    ('Valentina Perez',  'valentina.perez@email.com',  '3001000006', 'cliente', CLIENTE_PWD),
    ('Isabella Garcia',  'isabella.garcia@email.com',  '3001000007', 'cliente', CLIENTE_PWD),
    ('Laura Martinez',   'laura.martinez@email.com',   '3001000008', 'cliente', CLIENTE_PWD),
    ('Evelit Collante',  'evelit@gmail.co',            '3001000009', 'cliente', CLIENTE_PWD),
    ('Carlos Prieto',    'carlos@gmail.com',           '3001000010', 'cliente', 'carlos1234'),
]

conn = psycopg.connect(
    host=os.environ.get('DB_HOST','localhost'), port=os.environ.get('DB_PORT','5432'),
    dbname=os.environ.get('DB_NAME','Rossmix'), user=os.environ.get('DB_USER','postgres'),
    password=os.environ.get('DB_PASSWORD','')
)
cur = conn.cursor()

print('=' * 60)
print('INSERTANDO USUARIOS — ROSSMIX')
print('=' * 60)

creados = actualizados = 0
for nombre, email, telefono, tipo, pwd in USUARIOS:
    pwd_hash = generate_password_hash(pwd)
    cur.execute("SELECT id FROM usuario WHERE email = %s", (email,))
    existente = cur.fetchone()
    if existente:
        cur.execute("""UPDATE usuario SET nombre=%s, telefono=%s, tipo_usuario=%s, activo=TRUE
                       WHERE email=%s""", (nombre, telefono, tipo, email))
        actualizados += 1
        print(f'  [UPD  ] [{tipo:12}] {nombre:25} {email}')
    else:
        cur.execute("""INSERT INTO usuario (nombre, email, telefono, password, tipo_usuario)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (nombre, email, telefono, pwd_hash, tipo))
        creados += 1
        print(f'  [NUEVO] [{tipo:12}] {nombre:25} {email}')

conn.commit()

cur.execute("SELECT tipo_usuario, COUNT(*) FROM usuario GROUP BY tipo_usuario")
resumen = {r[0]: r[1] for r in cur.fetchall()}
total   = sum(resumen.values())
print(f'\nResultado: {creados} creados, {actualizados} actualizados')
print(f'Total en BD: {total} usuarios')
for tipo, cnt in sorted(resumen.items()):
    print(f'  {tipo:12}: {cnt}')
print(f'\nCredenciales:')
print(f'  Admin:   admin@rossmix.com       /  {ADMIN_PWD}')
print(f'  Cliente: andrea.vargas@email.com /  {CLIENTE_PWD}')
print(f'  Carlos:  carlos@gmail.com        /  carlos1234')
conn.close()

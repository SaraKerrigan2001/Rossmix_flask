"""
Crea/actualiza todos los usuarios de prueba de Rossmix en PostgreSQL.
Ejecutar una vez tras recrear la BD: python crear_usuarios.py
"""
import os, sys
# Agregar la raíz del proyecto al path (dos niveles arriba de scripts/utilidades/)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash

ADMIN_PWD   = os.environ.get('SEED_ADMIN_PASSWORD',  'admin123')
CLIENTE_PWD = os.environ.get('SEED_CLIENTE_PASSWORD', 'cliente123')

USUARIOS = [
    # (nombre, email, telefono, tipo, password)
    ('Administrador',    'admin@rossmix.com',            '3000000000', 'admin',   ADMIN_PWD),
    ('María González',   'maria@rossmix.com',            '3001000000', 'admin',   ADMIN_PWD),
    ('Andrea Vargas',    'andrea.vargas@email.com',       '3001000001', 'cliente', CLIENTE_PWD),
    ('Patricia Silva',   'patricia.silva@email.com',      '3001000002', 'cliente', CLIENTE_PWD),
    ('Diana Gutierrez',  'diana.gutierrez@email.com',     '3001000003', 'cliente', CLIENTE_PWD),
    ('Juliana Rojas',    'juliana.rojas@email.com',       '3001000004', 'cliente', CLIENTE_PWD),
    ('Catalina Mendoza', 'catalina.mendoza@email.com',    '3001000005', 'cliente', CLIENTE_PWD),
    ('Valentina Perez',  'valentina.perez@email.com',     '3001000006', 'cliente', CLIENTE_PWD),
    ('Isabella Garcia',  'isabella.garcia@email.com',     '3001000007', 'cliente', CLIENTE_PWD),
    ('Laura Martinez',   'laura.martinez@email.com',      '3001000008', 'cliente', CLIENTE_PWD),
    ('Evelit Collante',  'evelit@gmail.co',               '3001000009', 'cliente', CLIENTE_PWD),
    ('Carlos Prieto',    'carlos@gmail.com',              '3001000010', 'cliente', 'carlos1234'),
]

print('=' * 60)
print('CREANDO USUARIOS — ROSSMIX')
print('=' * 60)

app = create_app()
with app.app_context():
    creados = actualizados = 0
    for nombre, email, telefono, tipo, pwd in USUARIOS:
        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            existente.nombre       = nombre
            existente.telefono     = telefono
            existente.tipo_usuario = tipo
            existente.activo       = True
            actualizados += 1
            print(f'  [UPD  ] {tipo:7} {nombre:25} {email}')
        else:
            u = Usuario(
                nombre=nombre, email=email, telefono=telefono,
                password=generate_password_hash(pwd), tipo_usuario=tipo
            )
            db.session.add(u)
            creados += 1
            print(f'  [NUEVO] {tipo:7} {nombre:25} {email}')

    db.session.commit()

    total = Usuario.query.count()
    print(f'\nResultado: {creados} creados, {actualizados} actualizados — {total} usuarios en BD')
    print(f'\nCredenciales:')
    print(f'  Admin:   admin@rossmix.com  /  {ADMIN_PWD}')
    print(f'  Cliente: andrea.vargas@email.com  /  {CLIENTE_PWD}')
    print(f'  Carlos:  carlos@gmail.com  /  carlos1234')

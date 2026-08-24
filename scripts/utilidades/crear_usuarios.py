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
from app.models.empleado import Empleado
from werkzeug.security import generate_password_hash

ADMIN_PWD   = os.environ.get('SEED_ADMIN_PASSWORD',  'admin123')
CLIENTE_PWD = os.environ.get('SEED_CLIENTE_PASSWORD', 'cliente123')
ESPEC_PWD   = os.environ.get('SEED_ESPEC_PASSWORD',   'especialista123')

USUARIOS = [
    # (nombre, email, telefono, tipo, password, id_empleado)
    ('Administrador',    'admin@rossmix.com',            '3000000000', 'admin',   ADMIN_PWD, None),
    ('María González',   'maria@rossmix.com',            '3001000000', 'admin',   ADMIN_PWD, None),
    ('Andrea Vargas',    'andrea.vargas@email.com',       '3001000001', 'cliente', CLIENTE_PWD, None),
    ('Patricia Silva',   'patricia.silva@email.com',      '3001000002', 'cliente', CLIENTE_PWD, None),
    ('Diana Gutierrez',  'diana.gutierrez@email.com',     '3001000003', 'cliente', CLIENTE_PWD, None),
    ('Juliana Rojas',    'juliana.rojas@email.com',       '3001000004', 'cliente', CLIENTE_PWD, None),
    ('Catalina Mendoza', 'catalina.mendoza@email.com',    '3001000005', 'cliente', CLIENTE_PWD, None),
    ('Valentina Perez',  'valentina.perez@email.com',     '3001000006', 'cliente', CLIENTE_PWD, None),
    ('Isabella Garcia',  'isabella.garcia@email.com',     '3001000007', 'cliente', CLIENTE_PWD, None),
    ('Laura Martinez',   'laura.martinez@email.com',      '3001000008', 'cliente', CLIENTE_PWD, None),
    ('Evelit Collante',  'evelit@gmail.co',               '3001000009', 'cliente', CLIENTE_PWD, None),
    ('Carlos Prieto',    'carlos@gmail.com',              '3001000010', 'cliente', 'carlos1234', None),

    # Especialistas
    ('Ana Rodríguez',    'ana.rodriguez@rossmix.com',     '3100000000', 'especialista', ESPEC_PWD, 2),
    ('Laura Martínez',   'laura.martinez@rossmix.com',    '3100000000', 'especialista', ESPEC_PWD, 3),
    ('Sofía López',      'sofia.lopez@rossmix.com',       '3100000000', 'especialista', ESPEC_PWD, 4),
    ('Carolina Pérez',   'carolina.perez@rossmix.com',    '3100000000', 'especialista', ESPEC_PWD, 5),
    ('Valentina Torres', 'valentina.torres@rossmix.com',  '3100000000', 'especialista', ESPEC_PWD, 6),
    ('Daniela Ramírez',  'daniela.ramirez@rossmix.com',   '3100000000', 'especialista', ESPEC_PWD, 7),
    ('Camila Flores',    'camila.flores@rossmix.com',     '3100000000', 'especialista', ESPEC_PWD, 8),
    ('Isabella Castro',  'isabella.castro@rossmix.com',   '3100000000', 'especialista', ESPEC_PWD, 9),
    ('Gabriela Morales', 'gabriela.morales@rossmix.com',  '3100000000', 'especialista', ESPEC_PWD, 10),
]

print('=' * 60)
print('CREANDO USUARIOS — ROSSMIX')
print('=' * 60)

app = create_app()
with app.app_context():
    creados = actualizados = 0
    for nombre, email, telefono, tipo, pwd, id_emp in USUARIOS:
        if tipo == 'especialista':
            empleado = Empleado.query.filter_by(nombre=nombre).first()
            if not empleado:
                empleado = Empleado(
                    nombre=nombre,
                    especialidad='Especialista de belleza',
                    activo=True,
                )
                db.session.add(empleado)
                db.session.flush()
            id_emp = empleado.id_empleado

        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            existente.nombre       = nombre
            existente.telefono     = telefono
            existente.tipo_usuario = tipo
            existente.password     = generate_password_hash(pwd)
            existente.activo       = True
            existente.id_empleado  = id_emp
            actualizados += 1
            print(f'  [UPD  ] {tipo:12} {nombre:25} {email}')
        else:
            u = Usuario(
                nombre=nombre, email=email, telefono=telefono,
                password=generate_password_hash(pwd), tipo_usuario=tipo,
                id_empleado=id_emp
            )
            db.session.add(u)
            creados += 1
            print(f'  [NUEVO] {tipo:12} {nombre:25} {email}')

    db.session.commit()

    total = Usuario.query.count()
    print(f'\nResultado: {creados} creados, {actualizados} actualizados — {total} usuarios en BD')
    print(f'\nCredenciales:')
    print(f'  Admin:        admin@rossmix.com           /  {ADMIN_PWD}')
    print(f'  Cliente:      andrea.vargas@email.com     /  {CLIENTE_PWD}')
    print(f'  Especialista: ana.rodriguez@rossmix.com   /  {ESPEC_PWD}')

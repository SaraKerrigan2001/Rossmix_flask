"""
Sincroniza los usuarios originales del proyecto en la BD SQLite.
Asegura que los 4 correos indicados por la propietaria + el admin
existan con passwords funcionales (hasheados con Werkzeug).
"""
import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash, check_password_hash

app = create_app()

# Usuarios que DEBEN existir en la BD (segun crear_usuarios.py + lo indicado)
USUARIOS_REQUERIDOS = [
    # (nombre, email, telefono, password, tipo_usuario)
    ("Administrador",   "admin@rossmix.com",       "3000000000", "admin123",   "admin"),
    ("Maria Gonzalez",  "maria@rossmix.com",       "3001234567", "admin123",   "admin"),
    ("Andrea Vargas",   "andrea.vargas@email.com", "3100000001", "cliente123", "cliente"),
    ("Evelit Collante", "evelit@gmail.co",         "3100000009", "cliente123", "cliente"),
    ("Carlos Prieto",   "carlos@gmail.com",        "3456789123", "cliente123", "cliente"),
]

with app.app_context():
    print("=" * 60)
    print("  SINCRONIZACION DE USUARIOS EN LA BASE DE DATOS")
    print("=" * 60)
    print(f"  BD: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()

    for nombre, email, telefono, pwd, tipo in USUARIOS_REQUERIDOS:
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            # Verificar si la password actual funciona
            login_ok = check_password_hash(usuario.password, pwd)
            if login_ok:
                print(f"  [OK]      {email:30s} -> password '{pwd}' funciona")
            else:
                # Resetear password
                usuario.password = generate_password_hash(pwd)
                print(f"  [RESET]   {email:30s} -> password actualizada a '{pwd}'")
        else:
            # Crear usuario nuevo
            nuevo = Usuario(
                nombre=nombre,
                email=email,
                telefono=telefono,
                password=generate_password_hash(pwd),
                tipo_usuario=tipo
            )
            db.session.add(nuevo)
            print(f"  [CREADO]  {email:30s} -> tipo: {tipo}, password: '{pwd}'")

    try:
        db.session.commit()
        print("\n  Cambios guardados exitosamente.")
    except Exception as e:
        db.session.rollback()
        print(f"\n  ERROR al guardar: {e}")

    # Verificacion final
    print("\n" + "=" * 60)
    print("  TODOS LOS USUARIOS EN LA BASE DE DATOS")
    print("=" * 60)
    todos = Usuario.query.order_by(Usuario.tipo_usuario, Usuario.id).all()
    for u in todos:
        print(f"  ID:{u.id:3d} | {u.tipo_usuario:13s} | {u.email:30s} | {u.nombre}")

    print("\n" + "=" * 60)
    print("  CREDENCIALES PARA INICIAR SESION")
    print("=" * 60)
    print()
    print("  ADMINISTRADORES:")
    print("    admin@rossmix.com          / admin123")
    print("    maria@rossmix.com          / admin123")
    print()
    print("  CLIENTES:")
    print("    andrea.vargas@email.com    / cliente123")
    print("    evelit@gmail.co            / cliente123")
    print("    carlos@gmail.com           / cliente123")
    print()
    print("=" * 60)

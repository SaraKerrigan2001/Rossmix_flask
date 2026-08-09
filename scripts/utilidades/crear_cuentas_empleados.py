"""
Sincroniza los empleados sin cuenta en la BD SQLite asignándoles un rol de especialista y contraseña por defecto.
"""
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from app.models.empleado import Empleado
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("=" * 60)
    print("  CREACIÓN DE CUENTAS DE ESPECIALISTA")
    print("=" * 60)
    
    empleados = Empleado.query.all()
    contraseña_defecto = "especialista123"
    
    for emp in empleados:
        # Excluimos a María González que ya es administradora
        if emp.id_empleado == 1:
            print(f"Saltando {emp.nombre} (ID: 1) ya que cuenta con rol administrativo.")
            continue
            
        # Generar correo a partir del nombre
        nombre_limpio = emp.nombre.lower().replace(" ", ".").replace("í", "i").replace("ó", "o").replace("á", "a").replace("é", "e").replace("ú", "u").replace("ñ", "n")
        email = f"{nombre_limpio}@rossmix.com"
        
        # Verificar si la cuenta ya existe
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            # Crear cuenta de especialista vinculada
            nuevo_usuario = Usuario(
                nombre=emp.nombre,
                email=email,
                telefono="3100000000",
                password=generate_password_hash(contraseña_defecto),
                tipo_usuario="especialista",
                id_empleado=emp.id_empleado
            )
            db.session.add(nuevo_usuario)
            print(f"Creado: {emp.nombre:25s} | Email: {email:30s} | ID Empleado: {emp.id_empleado}")
        else:
            print(f"Ya existe: {email}")
            
    try:
        db.session.commit()
        print("\nCuentas creadas exitosamente.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar: {e}")

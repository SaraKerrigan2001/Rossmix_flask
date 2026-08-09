"""Verifica empleados en la BD y crea cuentas de usuario tipo especialista para cada uno."""
from dotenv import load_dotenv
load_dotenv()
from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from app.models.empleado import Empleado

app = create_app()
with app.app_context():
    print("=" * 70)
    print("  EMPLEADOS REGISTRADOS EN LA BASE DE DATOS")
    print("=" * 70)
    empleados = Empleado.query.order_by(Empleado.id_empleado).all()
    print(f"\n  Total empleados: {len(empleados)}")
    print("-" * 70)
    for e in empleados:
        # Buscar si tiene cuenta de usuario vinculada
        cuenta = Usuario.query.filter_by(id_empleado=e.id_empleado).first()
        tiene_cuenta = f"SI -> {cuenta.email}" if cuenta else "NO"
        print(f"  ID:{e.id_empleado:3d} | {e.nombre:25s} | {str(getattr(e, 'especialidad', 'N/A')):30s} | Activo: {e.activo} | Cuenta: {tiene_cuenta}")
    
    print("\n\n" + "=" * 70)
    print("  USUARIOS TIPO ESPECIALISTA")
    print("=" * 70)
    especialistas = Usuario.query.filter_by(tipo_usuario='especialista').all()
    if especialistas:
        for u in especialistas:
            print(f"  ID:{u.id:3d} | {u.nombre:25s} | {u.email:30s} | id_empleado: {u.id_empleado}")
    else:
        print("  No hay usuarios tipo especialista registrados.")
    print("=" * 70)

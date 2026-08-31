"""
Script completo para resetear IDs y repoblar la base de datos (Local o Docker).
Se asume que la variable de entorno DATABASE_URL dicta a qué base nos conectamos.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    try:
        # 1. Truncar todas las tablas y resetear secuencias (RESTART IDENTITY)
        print(f"[*] Conectando a la base de datos...")
        db.session.execute(db.text('TRUNCATE TABLE pagos, citas, empleado_servicios, horarios_empleados, servicios, empleados, usuario RESTART IDENTITY CASCADE;'))
        db.session.commit()
        print("[+] Tablas truncadas y secuencias reseteadas a 1.")

    except Exception as e:
        db.session.rollback()
        print(f"[-] Error reseteando la BD: {e}")
        sys.exit(1)

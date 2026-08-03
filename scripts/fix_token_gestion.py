"""
Agrega la columna token_gestion a la tabla citas en PostgreSQL.
Ejecutar una sola vez: python scripts/fix_token_gestion.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import importlib.util
spec = importlib.util.spec_from_file_location('app_module', 'app.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
app = m.app
db  = m.db

with app.app_context():
    # Verificar columnas que faltan en la tabla citas
    columnas_nuevas = [
        ("token_gestion", "ALTER TABLE citas ADD COLUMN token_gestion VARCHAR(32) UNIQUE"),
    ]

    for col, sql in columnas_nuevas:
        try:
            result = db.session.execute(db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='citas' AND column_name=:col"
            ), {"col": col}).fetchone()

            if result:
                print(f"  OK  columna '{col}' ya existe — sin cambios")
            else:
                db.session.execute(db.text(sql))
                db.session.commit()
                print(f"  OK  columna '{col}' agregada exitosamente a la tabla citas")

        except Exception as e:
            db.session.rollback()
            print(f"  ERROR en '{col}': {e}")

    # Verificar estado final
    print()
    result = db.session.execute(db.text(
        "SELECT column_name, data_type, character_maximum_length "
        "FROM information_schema.columns "
        "WHERE table_name='citas' "
        "ORDER BY ordinal_position"
    )).fetchall()
    print("Columnas actuales de la tabla citas:")
    for r in result:
        print(f"  {r[0]:25} {r[1]:20} {str(r[2]) if r[2] else ''}")

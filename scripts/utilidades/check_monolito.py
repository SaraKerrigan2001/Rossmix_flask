"""Verifica usuarios desde el contexto del monolito app.py (el que corre flask run)."""
import sys
sys.path.insert(0, '.')

# Importar directamente el monolito
import importlib
import importlib.util

# Cargar app.py como modulo con nombre distinto para no chocar con el paquete app/
spec = importlib.util.spec_from_file_location("app_monolito", "app.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

app_obj = mod.app
db_obj = mod.db
UsuarioModel = mod.Usuario

with app_obj.app_context():
    print("DB URI:", app_obj.config['SQLALCHEMY_DATABASE_URI'])
    usuarios = UsuarioModel.query.all()
    print(f"\nUsuarios en la BD del monolito: {len(usuarios)}")
    print("-" * 60)
    for u in usuarios:
        print(f"  {u.id:3d} | {u.tipo_usuario:13s} | {u.email:30s} | {u.nombre}")

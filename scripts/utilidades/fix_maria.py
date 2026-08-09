"""Corrige el tipo_usuario de maria@rossmix.com a admin."""
from dotenv import load_dotenv
load_dotenv()
from app import create_app
from app.extensions import db
from app.models.usuario import Usuario

app = create_app()
with app.app_context():
    u = Usuario.query.filter_by(email='maria@rossmix.com').first()
    if u:
        print(f"Antes:  {u.email} -> tipo_usuario = '{u.tipo_usuario}'")
        u.tipo_usuario = 'admin'
        db.session.commit()
        print(f"Ahora:  {u.email} -> tipo_usuario = '{u.tipo_usuario}'")
    else:
        print("Usuario maria@rossmix.com no encontrado")

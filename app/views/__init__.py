"""
Inicializa todas las vistas registrándolas como Blueprints de Flask.
"""
from app.views.main import main_bp
from app.views.auth import auth_bp
from app.views.cliente import cliente_bp
from app.views.citas import citas_bp
from app.views.notificaciones import notif_bp
from app.views.admin import admin_bp
from app.views.especialista import especialista_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'cliente_bp',
    'citas_bp',
    'notif_bp',
    'admin_bp',
    'especialista_bp',
]

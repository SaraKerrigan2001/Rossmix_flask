"""Decoradores de la aplicación."""
from functools import wraps
from flask import session, flash, redirect, url_for


def admin_required(f):
    """Decorador para requerir acceso de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('auth.login'))
        if session.get('tipo_usuario') != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('cliente.dashboard_cliente'))
        return f(*args, **kwargs)
    return decorated_function

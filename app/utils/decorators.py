"""Decoradores de la aplicación."""
from functools import wraps
from flask import session, flash, redirect, url_for
from app.extensions import db


def _usuario_activo_en_bd(tipo_requerido):
    """
    Verifica que el usuario de la sesión exista, esté activo en la BD
    y tenga el tipo requerido. Retorna el usuario si todo es válido, None si no.
    Importación tardía para evitar ciclos con db/models.
    """
    from app.models.usuario import Usuario
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return None
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario or not usuario.activo or usuario.tipo_usuario != tipo_requerido:
        return None
    return usuario


def admin_required(f):
    """
    Decorador para rutas de administrador.
    Verifica sesión, tipo_usuario == 'admin' Y que la cuenta esté activa en BD.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('auth.login'))

        # Verificación rápida por sesión antes de consultar la BD
        if session.get('tipo_usuario') != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('cliente.dashboard_cliente'))

        # Verificación en BD: cuenta puede haber sido desactivada desde el último login
        if not _usuario_activo_en_bd('admin'):
            session.clear()
            flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'error')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function


def especialista_required(f):
    """
    Decorador para rutas de especialista.
    Verifica sesión, tipo_usuario == 'especialista', cuenta activa en BD
    y que tenga un empleado vinculado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('auth.login'))

        if session.get('tipo_usuario') != 'especialista':
            flash('Acceso exclusivo para especialistas', 'error')
            return redirect(url_for('auth.login'))

        usuario = _usuario_activo_en_bd('especialista')
        if not usuario:
            session.clear()
            flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'error')
            return redirect(url_for('auth.login'))

        if not usuario.id_empleado:
            flash('Tu cuenta no tiene un empleado vinculado. Contacta al administrador.', 'error')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    """Decorador genérico: solo verifica que haya sesión activa."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

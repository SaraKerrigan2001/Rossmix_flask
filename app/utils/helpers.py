"""Funciones auxiliares compartidas."""
from flask import session
from app.extensions import db
from app.models.notificacion import Notificacion


def add_notificacion(id_usuario, titulo, mensaje=None, target=None):
    """Crear una notificación para un usuario."""
    try:
        n = Notificacion(id_usuario=id_usuario, titulo=titulo, mensaje=mensaje, target=target)
        db.session.add(n)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('Error al crear notificacion:', e)


def inject_notificaciones():
    """Context processor: inyecta notificaciones en todos los templates."""
    if 'usuario_id' in session:
        try:
            notifs = Notificacion.query.filter_by(
                id_usuario=session['usuario_id']).order_by(
                Notificacion.fecha.desc()).limit(6).all()
            unread = Notificacion.query.filter_by(id_usuario=session['usuario_id'], leido=False).count()
            return dict(notificaciones=notifs, notificaciones_unread=unread)
        except Exception:
            return dict(notificaciones=[], notificaciones_unread=0)
    return dict(notificaciones=[], notificaciones_unread=0)

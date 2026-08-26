"""Vistas de notificaciones."""
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from app.extensions import db
from app.models import Notificacion

notif_bp = Blueprint('notif', __name__)


@notif_bp.route('/notificaciones')
def notificaciones():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))
    # Paginación simple
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q = Notificacion.query.filter_by(id_usuario=session['usuario_id']).order_by(Notificacion.fecha.desc())
    total = q.count()
    total_pages = (total + per_page - 1) // per_page
    notifs = q.offset((page - 1) * per_page).limit(per_page).all()
    return render_template('notificaciones.html', notificaciones=notifs, page=page, total_pages=total_pages)


# Marcar una notificación como leída
@notif_bp.route('/notificaciones/marcar-leida/<int:notif_id>', methods=['POST'])
def marcar_leida(notif_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    n = db.get_or_404(Notificacion, notif_id)
    # permitir solo al propietario de la notificación o a admins
    if n.id_usuario != session['usuario_id'] and session.get('tipo_usuario') != 'admin':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    n.leido = True
    db.session.commit()
    # devolver nuevo conteo de no leídos
    unread = Notificacion.query.filter_by(id_usuario=session['usuario_id'], leido=False).count()
    return jsonify({'success': True, 'unread': unread})


# Marcar todas las notificaciones del usuario como leídas
@notif_bp.route('/notificaciones/marcar-todas', methods=['POST'])
def marcar_todas():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    try:
        Notificacion.query.filter_by(id_usuario=session['usuario_id'], leido=False).update({'leido': True})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': True, 'unread': 0})

"""Vistas del dashboard de cliente."""
from flask import Blueprint, render_template, session, flash, redirect, url_for
from datetime import datetime
from app.extensions import db
from app.models import Usuario, Cita, Servicio, Empleado

cliente_bp = Blueprint('cliente', __name__)


@cliente_bp.route('/dashboard/cliente')
def dashboard_cliente():
    if 'usuario_id' not in session or session.get('tipo_usuario') != 'cliente':
        flash('Debes iniciar sesión como cliente', 'error')
        return redirect(url_for('auth.login'))

    id_cliente = session['usuario_id']

    # Citas pendientes/confirmadas (futuras)
    citas_pendientes = Cita.query.filter(
        Cita.id_cliente == id_cliente,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    # Citas completadas
    citas_completadas = Cita.query.filter(
        Cita.id_cliente == id_cliente,
        Cita.estado == 'completada'
    ).count()

    # Próxima cita
    proxima_cita = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).outerjoin(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).filter(
        Cita.id_cliente == id_cliente,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).order_by(Cita.fecha_hora_inicio).first()

    stats = {
        'citas_pendientes': citas_pendientes,
        'citas_completadas': citas_completadas
    }

    return render_template('dashboard_cliente.html', stats=stats, proxima_cita=proxima_cita)

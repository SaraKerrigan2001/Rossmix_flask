"""Gestión de citas (admin)."""
from datetime import datetime, timedelta
from flask import render_template, request, jsonify
from app.extensions import db
from app.models import Usuario, Empleado, Servicio, Cita
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/citas')
@admin_required
def citas():
    """Listar todas las citas"""
    # Filtros
    estado = request.args.get('estado', 'todas')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    query = db.session.query(Cita, Usuario, Empleado, Servicio).join(
        Usuario, Cita.id_cliente == Usuario.id
    ).join(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    )

    # Aplicar filtros
    if estado != 'todas':
        query = query.filter(Cita.estado == estado)

    # Filtrar por cliente si se pasa cliente_id
    cliente_id = request.args.get('cliente_id')
    if cliente_id:
        try:
            cid = int(cliente_id)
            query = query.filter(Cita.id_cliente == cid)
        except ValueError:
            pass

    if fecha_desde:
        fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query = query.filter(Cita.fecha_hora_inicio >= fecha_desde_dt)

    if fecha_hasta:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Cita.fecha_hora_inicio < fecha_hasta_dt)

    lista_citas = query.order_by(Cita.fecha_hora_inicio.desc()).all()

    # Si se filtró por cliente, obtener objeto para mostrar en la cabecera
    cliente_filtrado = None
    if cliente_id:
        try:
            cliente_filtrado = Usuario.query.get(int(cliente_id))
        except Exception:
            cliente_filtrado = None

    return render_template('admin/citas.html', citas=lista_citas, estado_filtro=estado, cliente_filtrado=cliente_filtrado)


@admin_bp.route('/citas/cambiar-estado/<int:id_cita>', methods=['POST'])
@admin_required
def citas_cambiar_estado(id_cita):
    """Cambiar estado de una cita"""
    cita = Cita.query.get_or_404(id_cita)
    nuevo_estado = request.form.get('estado')

    estados_validos = ['pendiente_pago', 'confirmada', 'en_atencion', 'completada', 'cancelada', 'no_asistio']

    if nuevo_estado not in estados_validos:
        return jsonify({'success': False, 'message': 'Estado inválido'}), 400

    cita.estado = nuevo_estado
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Estado de cita actualizado a {nuevo_estado}'
    })

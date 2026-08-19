"""Gestión de citas (admin) — incluye reasignación y distribución."""
from datetime import datetime, timedelta
from flask import render_template, request, jsonify
from sqlalchemy import outerjoin
from app.extensions import db
from app.models import Usuario, Empleado, Servicio, Cita, EmpleadoServicio
from app.utils.decorators import admin_required
from app.utils.helpers import add_notificacion
from app.views.admin import admin_bp


@admin_bp.route('/citas')
@admin_required
def citas():
    """Listar todas las citas — LEFT JOIN para incluir las sin especialista"""
    estado     = request.args.get('estado', 'todas')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    cliente_id  = request.args.get('cliente_id')

    # LEFT OUTER JOIN en Empleado para ver citas sin especialista asignada
    query = db.session.query(Cita, Usuario, Empleado, Servicio)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .outerjoin(Empleado, Cita.id_empleado == Empleado.id_empleado)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)

    if estado != 'todas':
        query = query.filter(Cita.estado == estado)

    if cliente_id:
        try:
            query = query.filter(Cita.id_cliente == int(cliente_id))
        except ValueError:
            pass

    if fecha_desde:
        query = query.filter(
            Cita.fecha_hora_inicio >= datetime.strptime(fecha_desde, '%Y-%m-%d')
        )
    if fecha_hasta:
        query = query.filter(
            Cita.fecha_hora_inicio < datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
        )

    lista_citas = query.order_by(Cita.fecha_hora_inicio.desc()).all()

    cliente_filtrado = None
    if cliente_id:
        try:
            cliente_filtrado = db.session.get(Usuario, int(cliente_id))
        except Exception:
            pass

    # Contar citas sin asignar activas
    sin_asignar = Cita.query.filter(
        Cita.id_empleado.is_(None),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    return render_template(
        'admin/citas.html',
        citas=lista_citas,
        estado_filtro=estado,
        cliente_filtrado=cliente_filtrado,
        sin_asignar=sin_asignar
    )


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
    return jsonify({'success': True, 'message': f'Estado actualizado a {nuevo_estado}'})


# ── Reasignar especialista ────────────────────────────────────────────────────

@admin_bp.route('/citas/reasignar-empleado/<int:id_cita>', methods=['GET', 'POST'])
@admin_required
def citas_reasignar_empleado(id_cita):
    """GET: empleados disponibles para la cita | POST: asignar"""
    cita = Cita.query.get_or_404(id_cita)
    cliente = db.session.get(Usuario, cita.id_cliente)
    servicio = db.session.get(Servicio, cita.id_servicio)

    if request.method == 'GET':
        emp_ids = [e.id_empleado for e in EmpleadoServicio.query.filter_by(id_servicio=cita.id_servicio).all()]
        empleados = Empleado.query.filter(
            Empleado.id_empleado.in_(emp_ids),
            Empleado.activo == True
        ).all()
        return jsonify({
            'cliente':   cliente.nombre if cliente else '—',
            'servicio':  servicio.nombre_servicio if servicio else '—',
            'fecha':     cita.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M'),
            'empleados': [{'id': e.id_empleado, 'nombre': e.nombre,
                           'especialidad': e.especialidad or 'Sin especialidad'} for e in empleados]
        })

    # POST
    id_empleado = request.form.get('id_empleado', type=int)
    if not id_empleado:
        return jsonify({'success': False, 'message': 'Falta id_empleado'}), 400

    empleado = Empleado.query.get_or_404(id_empleado)
    cita.id_empleado = id_empleado
    if cita.estado == 'pendiente_pago':
        cita.estado = 'confirmada'
    db.session.commit()

    # Notificar al cliente
    try:
        add_notificacion(
            cita.id_cliente,
            'Especialista asignada',
            f'Tu cita del {cita.fecha_hora_inicio.strftime("%d/%m/%Y")} ha sido asignada a {empleado.nombre}.'
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': f'Cita asignada a {empleado.nombre}',
        'empleado_nombre': empleado.nombre
    })


# ── Clientes afectados al eliminar un empleado ────────────────────────────────

@admin_bp.route('/empleados/clientes-afectados/<int:id_empleado>')
@admin_required
def empleados_clientes_afectados(id_empleado):
    """Citas futuras activas del empleado que afectarán a clientes"""
    citas = db.session.query(Cita, Usuario, Servicio)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .filter(
            Cita.id_empleado == id_empleado,
            Cita.fecha_hora_inicio >= datetime.now(),
            Cita.estado.in_(['pendiente_pago', 'confirmada'])
        ).order_by(Cita.fecha_hora_inicio).all()

    return jsonify({
        'total': len(citas),
        'afectados': [{
            'cliente':  u.nombre,
            'telefono': u.telefono,
            'servicio': s.nombre_servicio,
            'fecha':    c.fecha_hora_inicio.strftime('%d/%m/%Y'),
            'hora':     c.fecha_hora_inicio.strftime('%H:%M'),
        } for c, u, s in citas]
    })


# ── Panel de distribución de citas ───────────────────────────────────────────

@admin_bp.route('/citas/distribucion')
@admin_required
def citas_distribucion():
    """Panel para asignar citas sin especialista entre las disponibles"""
    # Citas activas sin asignar
    sin_asignar = db.session.query(Cita, Usuario, Servicio)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .filter(
            Cita.id_empleado.is_(None),
            Cita.estado.in_(['pendiente_pago', 'confirmada'])
        ).order_by(Cita.fecha_hora_inicio).all()

    # Todas las especialistas activas con sus citas futuras
    empleados = Empleado.query.filter_by(activo=True).order_by(Empleado.nombre).all()
    carga = {}
    for emp in empleados:
        carga[emp.id_empleado] = Cita.query.filter(
            Cita.id_empleado == emp.id_empleado,
            Cita.fecha_hora_inicio >= datetime.now(),
            Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion'])
        ).count()

    return render_template(
        'admin/distribucion_citas.html',
        sin_asignar=sin_asignar,
        empleados=empleados,
        carga=carga
    )


@admin_bp.route('/citas/asignar-batch', methods=['POST'])
@admin_required
def citas_asignar_batch():
    """Asignar múltiples citas sin especialista de una vez"""
    asignaciones = request.get_json(force=True) or []
    # formato: [{"id_cita": 5, "id_empleado": 3}, ...]
    errores = []
    ok = 0
    for item in asignaciones:
        try:
            cita = db.session.get(Cita, item['id_cita'])
            emp  = db.session.get(Empleado, item['id_empleado'])
            if not cita or not emp:
                errores.append(f"Cita {item.get('id_cita')} o empleado no encontrado")
                continue
            cita.id_empleado = emp.id_empleado
            if cita.estado == 'pendiente_pago':
                cita.estado = 'confirmada'
            ok += 1
            try:
                add_notificacion(
                    cita.id_cliente,
                    'Especialista asignada',
                    f'Tu cita del {cita.fecha_hora_inicio.strftime("%d/%m/%Y")} fue asignada a {emp.nombre}.'
                )
            except Exception:
                pass
        except Exception as e:
            errores.append(str(e))

    db.session.commit()
    return jsonify({
        'success': True,
        'asignadas': ok,
        'errores': errores
    })

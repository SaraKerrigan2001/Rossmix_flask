"""Vistas del sistema de citas (agendamiento, cancelación, pagos cliente)."""
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.extensions import db
from app.models import Usuario, Cita, Servicio, Empleado, EmpleadoServicio, HorarioEmpleado
from app.utils.helpers import add_notificacion

citas_bp = Blueprint('citas', __name__)


@citas_bp.route('/citas/agendar/paso1')
def agendar_paso1():
    """Paso 1: Seleccionar servicio"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('auth.login'))

    # Obtener todos los servicios activos
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre_servicio).all()

    return render_template('citas/paso1_servicio.html', servicios=servicios)


@citas_bp.route('/citas/agendar/paso2/<int:id_servicio>')
def agendar_paso2(id_servicio):
    """Paso 2: Seleccionar empleado o aleatorio"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('auth.login'))

    # Obtener servicio seleccionado
    servicio = Servicio.query.get_or_404(id_servicio)

    # Obtener empleados que realizan este servicio
    empleados_ids = db.session.query(EmpleadoServicio.id_empleado).filter_by(id_servicio=id_servicio).all()
    empleados_ids = [e[0] for e in empleados_ids]

    empleados = Empleado.query.filter(
        Empleado.id_empleado.in_(empleados_ids),
        Empleado.activo
    ).all()

    return render_template('citas/paso2_empleado.html', servicio=servicio, empleados=empleados)


@citas_bp.route('/citas/agendar/paso3/<int:id_servicio>/<int:id_empleado>')
def agendar_paso3(id_servicio, id_empleado):
    """Paso 3: Seleccionar fecha y hora"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('auth.login'))

    servicio = Servicio.query.get_or_404(id_servicio)
    empleado = Empleado.query.get_or_404(id_empleado) if id_empleado > 0 else None

    # Fechas para el template
    hoy = datetime.now().strftime('%Y-%m-%d')
    max_fecha = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

    return render_template('citas/paso3_fecha_hora.html',
                           servicio=servicio,
                           empleado=empleado,
                           hoy=hoy,
                           max_fecha=max_fecha)


@citas_bp.route('/citas/horarios-disponibles')
def horarios_disponibles():
    """API: Obtener horarios disponibles para una fecha y empleado"""
    fecha_str = request.args.get('fecha')
    id_empleado = request.args.get('id_empleado', type=int)
    id_servicio = request.args.get('id_servicio', type=int)

    if not all([fecha_str, id_servicio]):
        return jsonify({'error': 'Faltan parámetros'}), 400

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except BaseException:
        return jsonify({'error': 'Fecha inválida'}), 400

    # Si id_empleado es 0, seleccionar empleado aleatorio que haga el servicio
    if id_empleado == 0:
        empleados_ids = db.session.query(EmpleadoServicio.id_empleado).filter_by(id_servicio=id_servicio).all()
        empleados_ids = [e[0] for e in empleados_ids]
        if not empleados_ids:
            return jsonify({'horarios': []})
        id_empleado = random.choice(empleados_ids)

    # Obtener servicio para duración
    servicio = Servicio.query.get(id_servicio)
    if not servicio:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    # Obtener día de la semana (0=Domingo, 1=Lunes, etc.)
    dia_semana = (fecha.weekday() + 1) % 7  # Convertir de Python (0=Lunes) a nuestra DB (0=Domingo)

    # Obtener horario del empleado para ese día
    horario = HorarioEmpleado.query.filter_by(
        id_empleado=id_empleado,
        dia_semana=dia_semana
    ).first()

    if not horario:
        return jsonify({'horarios': []})

    # Generar slots de tiempo disponibles
    horarios_list = []
    hora_actual = datetime.combine(fecha, horario.hora_inicio)
    hora_fin = datetime.combine(fecha, horario.hora_fin)
    duracion = timedelta(minutes=servicio.duracion_minutos)

    while hora_actual + duracion <= hora_fin:
        # Verificar si ya hay una cita en este horario
        cita_existente = Cita.query.filter(
            Cita.id_empleado == id_empleado,
            Cita.fecha_hora_inicio < hora_actual + duracion,
            Cita.fecha_hora_fin > hora_actual,
            Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion'])
        ).first()

        if not cita_existente:
            horarios_list.append({
                'hora': hora_actual.strftime('%H:%M'),
                'hora_fin': (hora_actual + duracion).strftime('%H:%M'),
                'disponible': True
            })

        hora_actual += timedelta(minutes=30)  # Intervalos de 30 minutos

    return jsonify({
        'horarios': horarios_list,
        'id_empleado': id_empleado
    })


@citas_bp.route('/citas/agendar/paso4', methods=['POST'])
def agendar_paso4():
    """Paso 4: Confirmación y pago"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('auth.login'))

    # Obtener datos del formulario
    id_servicio = request.form.get('id_servicio', type=int)
    id_empleado = request.form.get('id_empleado', type=int)
    fecha_str = request.form.get('fecha')
    hora_str = request.form.get('hora')

    if not all([id_servicio, fecha_str, hora_str]):
        flash('Datos incompletos', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    # Obtener información
    servicio = Servicio.query.get_or_404(id_servicio)
    empleado = Empleado.query.get_or_404(id_empleado) if id_empleado > 0 else None

    # Parsear fecha y hora
    try:
        fecha_hora_inicio = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
        fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=servicio.duracion_minutos)
    except BaseException:
        flash('Fecha u hora inválida', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    # Validar que la fecha sea futura
    if fecha_hora_inicio < datetime.now():
        flash('No puedes agendar citas en el pasado', 'error')
        return redirect(url_for('citas.agendar_paso3', id_servicio=id_servicio, id_empleado=id_empleado or 0))

    return render_template('citas/paso4_confirmacion.html',
                           servicio=servicio,
                           empleado=empleado,
                           fecha_hora_inicio=fecha_hora_inicio,
                           fecha_hora_fin=fecha_hora_fin,
                           id_empleado=id_empleado or 0)


@citas_bp.route('/citas/confirmar', methods=['POST'])
def confirmar_cita():
    """Confirmar y crear la cita"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    # Obtener datos
    id_servicio = request.form.get('id_servicio', type=int)
    id_empleado = request.form.get('id_empleado', type=int)
    fecha_hora_inicio_str = request.form.get('fecha_hora_inicio')
    fecha_hora_fin_str = request.form.get('fecha_hora_fin')

    try:
        fecha_hora_inicio = datetime.strptime(fecha_hora_inicio_str, '%Y-%m-%d %H:%M:%S')
        fecha_hora_fin = datetime.strptime(fecha_hora_fin_str, '%Y-%m-%d %H:%M:%S')
    except BaseException:
        flash('Error en las fechas', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    # Obtener servicio
    servicio = Servicio.query.get(id_servicio)
    if not servicio:
        flash('Servicio no encontrado', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    # Si empleado es 0, asignar aleatorio
    if id_empleado == 0:
        empleados_ids = db.session.query(EmpleadoServicio.id_empleado).filter_by(id_servicio=id_servicio).all()
        empleados_ids = [e[0] for e in empleados_ids]
        if empleados_ids:
            id_empleado = random.choice(empleados_ids)
        else:
            flash('No hay empleados disponibles para este servicio', 'error')
            return redirect(url_for('citas.agendar_paso1'))

    # Generar código de reserva
    codigo_reserva = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Crear cita
    nueva_cita = Cita(
        id_cliente=session['usuario_id'],
        id_empleado=id_empleado,
        id_servicio=id_servicio,
        fecha_hora_inicio=fecha_hora_inicio,
        fecha_hora_fin=fecha_hora_fin,
        monto_total=Decimal(str(servicio.precio_total)),
        monto_abono=Decimal('5000.00'),
        saldo_pendiente=Decimal(str(servicio.precio_total)) - Decimal('5000.00'),
        estado='pendiente_pago',
        reembolsado=False,
        codigo_reserva=codigo_reserva,
        fecha_creacion=datetime.now()
    )

    try:
        db.session.add(nueva_cita)
        db.session.commit()
        flash('¡Cita agendada exitosamente!', 'success')
        return redirect(url_for('citas.cita_confirmada', codigo=codigo_reserva))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la cita: {str(e)}', 'error')
        return redirect(url_for('citas.agendar_paso1'))


@citas_bp.route('/citas/confirmada/<codigo>')
def cita_confirmada(codigo):
    """Mostrar detalles de cita confirmada"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))

    cita = Cita.query.filter_by(codigo_reserva=codigo, id_cliente=session['usuario_id']).first_or_404()
    servicio = Servicio.query.get(cita.id_servicio)
    empleado = Empleado.query.get(cita.id_empleado)

    return render_template('citas/confirmada.html', cita=cita, servicio=servicio, empleado=empleado)


@citas_bp.route('/citas/mis-citas')
def mis_citas():
    """Ver mis citas agendadas"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))

    # Obtener citas futuras
    citas_futuras = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).join(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).filter(
        Cita.id_cliente == session['usuario_id'],
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).order_by(Cita.fecha_hora_inicio).all()

    # Obtener citas pasadas
    citas_pasadas = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).join(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).filter(
        Cita.id_cliente == session['usuario_id'],
        Cita.fecha_hora_inicio < datetime.now()
    ).order_by(Cita.fecha_hora_inicio.desc()).limit(10).all()

    # Pasar función now para calcular tiempo restante en el template
    return render_template('citas/mis_citas.html',
                           citas_futuras=citas_futuras,
                           citas_pasadas=citas_pasadas,
                           now=datetime.now)


@citas_bp.route('/citas/cancelar/<int:id_cita>', methods=['POST'])
def cancelar_cita(id_cita):
    """Cancelar una cita"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    cita = Cita.query.filter_by(id_cita=id_cita, id_cliente=session['usuario_id']).first()

    if not cita:
        return jsonify({'error': 'Cita no encontrada'}), 404

    # Validar que falten al menos 2 horas
    tiempo_restante = cita.fecha_hora_inicio - datetime.now()
    if tiempo_restante < timedelta(hours=2):
        return jsonify({'error': 'Debes cancelar con mínimo 2 horas de anticipación'}), 400

    # Cancelar cita
    cita.estado = 'cancelada'
    db.session.commit()

    # Notificar al cliente
    try:
        add_notificacion(
            cita.id_cliente,
            'Cita cancelada',
            f'Tu cita programada para {cita.fecha_hora_inicio.strftime("%d/%m/%Y %H:%M")} ha sido cancelada.',
            target=url_for('citas.mis_citas')
        )
    except Exception:
        pass

    # Notificar a administradores
    try:
        admins = Usuario.query.filter_by(tipo_usuario='admin').all()
        for a in admins:
            add_notificacion(
                a.id,
                'Cita cancelada',
                f'El cliente {cita.cliente.nombre if cita.cliente else cita.id_cliente} canceló la cita #{cita.id_cita} programada para {cita.fecha_hora_inicio.strftime("%d/%m/%Y %H:%M")}',
                target=url_for('admin.citas') +
                f'?estado=cancelada&cliente_id={cita.id_cliente}')
    except Exception:
        pass

    return jsonify({'success': True, 'message': 'Cita cancelada exitosamente'})


@citas_bp.route('/citas/pagar/<int:id_cita>', methods=['GET', 'POST'])
def cliente_pagos_registrar(id_cita):
    """Registrar pago para una cita por el cliente"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para realizar un pago', 'error')
        return redirect(url_for('auth.login'))

    from app.models import Pago

    cita = Cita.query.get_or_404(id_cita)

    # Ensure the appointment belongs to the logged in user
    if cita.id_cliente != session['usuario_id']:
        flash('No tienes permiso para pagar esta cita', 'error')
        return redirect(url_for('citas.mis_citas'))

    cliente = Usuario.query.get(cita.id_cliente)
    servicio = Servicio.query.get(cita.id_servicio)

    # Verificar que no tenga ya un pago o no esté cancelada
    if cita.pago:
        flash('Esta cita ya tiene un pago registrado', 'error')
        return redirect(url_for('citas.mis_citas'))

    if cita.estado == 'cancelada':
        flash('No puedes pagar una cita cancelada', 'error')
        return redirect(url_for('citas.mis_citas'))

    if request.method == 'POST':
        monto = request.form.get('monto', type=float)
        metodo = request.form.get('metodo_pago', 'efectivo')
        referencia = request.form.get('referencia', '').strip() or None
        notas = request.form.get('notas', '').strip() or None

        if not monto or monto <= 0:
            flash('El monto debe ser mayor a 0', 'error')
            return redirect(url_for('citas.cliente_pagos_registrar', id_cita=id_cita))

        metodos_validos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
        if metodo not in metodos_validos:
            flash('Método de pago inválido', 'error')
            return redirect(url_for('citas.cliente_pagos_registrar', id_cita=id_cita))

        nuevo_pago = Pago(
            id_cita=id_cita,
            monto=Decimal(str(monto)),
            metodo_pago=metodo,
            estado_pago='completado',
            referencia=referencia,
            notas=notas
        )
        db.session.add(nuevo_pago)

        # Actualizar estado de cita y saldo
        cita.monto_abono = (cita.monto_abono or Decimal('0')) + Decimal(str(monto))
        cita.saldo_pendiente = (cita.monto_total or Decimal('0')) - cita.monto_abono
        if cita.saldo_pendiente <= 0:
            cita.estado = 'completada'
            cita.saldo_pendiente = Decimal('0')

        db.session.commit()

        # Notificar a administradores
        try:
            admins = Usuario.query.filter_by(tipo_usuario='admin').all()
            for a in admins:
                add_notificacion(
                    a.id,
                    'Pago registrado por cliente',
                    f'Pago de ${monto:,.0f} registrado por el cliente {cliente.nombre} para la cita #{cita.id_cita}',
                    target=url_for('admin.pagos')
                )
        except Exception:
            pass

        flash(f'Pago de ${monto:,.0f} registrado exitosamente', 'success')
        return redirect(url_for('citas.mis_citas'))

    # GET — formulario
    metodos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
    return render_template('citas/cliente_pagos_form.html',
                           cita=cita, cliente=cliente,
                           servicio=servicio, metodos=metodos)

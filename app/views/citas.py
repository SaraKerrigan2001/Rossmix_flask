"""Vistas del sistema de citas (agendamiento, cancelación, pagos cliente)."""
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.extensions import db
from app.forms.auth import PagoForm
from app.forms.citas import SeleccionarHorarioForm, ConfirmarCitaForm
from app.models import Usuario, Cita, Servicio, Empleado, EmpleadoServicio, HorarioEmpleado
from app.services.citas_service import CitaService
from app.utils.helpers import add_notificacion

citas_bp = Blueprint('citas', __name__)


@citas_bp.route('/citas/estado/<int:id_cita>')
def estado_cita(id_cita):
    """API: Retorna el estado actual de una cita (usado por polling en mis_citas y confirmada)."""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    cita = Cita.query.filter_by(
        id_cita=id_cita, id_cliente=session['usuario_id']
    ).first_or_404()
    return jsonify({'estado': cita.estado, 'id_cita': cita.id_cita})


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

    form = SeleccionarHorarioForm(
        id_servicio=servicio.id_servicio,
        id_empleado=empleado.id_empleado if empleado else 0
    )

    return render_template('citas/paso3_fecha_hora.html',
                           servicio=servicio,
                           empleado=empleado,
                           hoy=hoy,
                           max_fecha=max_fecha,
                           form=form)


@citas_bp.route('/citas/horarios-disponibles')
def horarios_disponibles():
    """API: Obtener horarios disponibles para una fecha y empleado"""
    fecha_str   = request.args.get('fecha')
    id_empleado = request.args.get('id_empleado', type=int)
    id_servicio = request.args.get('id_servicio', type=int)

    if not all([fecha_str, id_servicio]):
        return jsonify({'error': 'Faltan parámetros'}), 400

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Fecha inválida'}), 400

    # Delegar completamente al servicio — evita duplicación de lógica
    horarios = CitaService.obtener_horarios_disponibles(        fecha=fecha,
        id_servicio=id_servicio,
        id_empleado=id_empleado or 0,
    )

    # Si el empleado fue 0, el servicio elige uno aleatoriamente internamente;
    # necesitamos devolver cuál fue elegido para que el paso 4 lo use.
    # Re-ejecutamos solo para obtener el id_empleado resuelto.
    id_empleado_resuelto = id_empleado or 0
    if id_empleado_resuelto == 0 and horarios:
        ids = [e.id_empleado for e in EmpleadoServicio.query.filter_by(id_servicio=id_servicio).all()]
        if ids:
            id_empleado_resuelto = random.choice(ids)

    return jsonify({
        'horarios': horarios,
        'id_empleado': id_empleado_resuelto,
    })


@citas_bp.route('/citas/agendar/paso4', methods=['POST'])
def agendar_paso4():
    """Paso 4: Confirmación y pago"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('auth.login'))

    form = SeleccionarHorarioForm()
    if not form.validate_on_submit():
        flash('Datos incompletos o inválidos', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    id_servicio = int(form.id_servicio.data)
    id_empleado = int(form.id_empleado.data or 0)
    fecha_str = form.fecha.data
    hora_str = form.hora.data

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

    confirmation_form = ConfirmarCitaForm(
        id_servicio=id_servicio,
        id_empleado=id_empleado,
        fecha_hora_inicio=fecha_hora_inicio.strftime('%Y-%m-%d %H:%M:%S'),
        fecha_hora_fin=fecha_hora_fin.strftime('%Y-%m-%d %H:%M:%S')
    )

    return render_template('citas/paso4_confirmacion.html',
                           servicio=servicio,
                           empleado=empleado,
                           fecha_hora_inicio=fecha_hora_inicio,
                           fecha_hora_fin=fecha_hora_fin,
                           id_empleado=id_empleado or 0,
                           form=confirmation_form)


@citas_bp.route('/citas/confirmar', methods=['POST'])
def confirmar_cita():
    """Confirmar y crear la cita"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    form = ConfirmarCitaForm()
    if not form.validate_on_submit():
        flash('La confirmación de la cita falló. Por favor vuelve a intentarlo.', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    id_servicio = int(form.id_servicio.data)
    id_empleado = int(form.id_empleado.data or 0)
    fecha_hora_inicio_str = form.fecha_hora_inicio.data
    fecha_hora_fin_str = form.fecha_hora_fin.data

    try:
        fecha_hora_inicio = datetime.strptime(fecha_hora_inicio_str, '%Y-%m-%d %H:%M:%S')
        fecha_hora_fin = datetime.strptime(fecha_hora_fin_str, '%Y-%m-%d %H:%M:%S')
    except BaseException:
        flash('Error en las fechas', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    # ── Validaciones de negocio contra manipulación de campos ocultos ─────────

    # 1. El servicio debe existir y estar activo
    servicio = db.session.get(Servicio, id_servicio)
    if not servicio or not servicio.activo:
        flash('Servicio no válido o inactivo.', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    # 2. El empleado debe estar activo y ofrecer el servicio
    if id_empleado == 0:
        empleados_ids = db.session.query(EmpleadoServicio.id_empleado).join(
            Empleado, EmpleadoServicio.id_empleado == Empleado.id_empleado
        ).filter(
            EmpleadoServicio.id_servicio == id_servicio,
            Empleado.activo == True
        ).all()
        empleados_ids = [e[0] for e in empleados_ids]
        if not empleados_ids:
            flash('No hay especialistas disponibles para este servicio.', 'error')
            return redirect(url_for('citas.agendar_paso1'))
        id_empleado = random.choice(empleados_ids)
    else:
        empleado = db.session.get(Empleado, id_empleado)
        if not empleado or not empleado.activo:
            flash('La especialista seleccionada no está disponible.', 'error')
            return redirect(url_for('citas.agendar_paso1'))
        ofrece_servicio = EmpleadoServicio.query.filter_by(
            id_empleado=id_empleado, id_servicio=id_servicio
        ).first()
        if not ofrece_servicio:
            flash('La especialista no realiza el servicio seleccionado.', 'error')
            return redirect(url_for('citas.agendar_paso1'))

    # 3. La duración de la cita debe coincidir con la duración real del servicio
    duracion_real = timedelta(minutes=servicio.duracion_minutos)
    if (fecha_hora_fin - fecha_hora_inicio) != duracion_real:
        # Corregir la fecha_hora_fin en lugar de rechazar
        fecha_hora_fin = fecha_hora_inicio + duracion_real

    # 4. La fecha debe ser futura (mínimo 30 min de anticipación)
    if fecha_hora_inicio < datetime.now() + timedelta(minutes=30):
        flash('La cita debe ser con al menos 30 minutos de anticipación.', 'error')
        return redirect(url_for('citas.agendar_paso1'))

    # 5. Verificar disponibilidad real del empleado
    if not CitaService.validar_disponibilidad_cita(id_empleado, fecha_hora_inicio, fecha_hora_fin):
        flash('El horario seleccionado ya no está disponible. Por favor elige otro.', 'error')
        return redirect(url_for('citas.agendar_paso3', id_servicio=id_servicio, id_empleado=id_empleado))

    try:
        nueva_cita = CitaService.crear_cita(
            id_cliente=session['usuario_id'],
            id_servicio=id_servicio,
            id_empleado=id_empleado,
            fecha_hora_inicio=fecha_hora_inicio,
            fecha_hora_fin=fecha_hora_fin
        )

        # Aplicar crédito de reagenda si existe en sesión
        credito = session.pop('credito_reagenda', None)
        if credito and credito.get('monto_credito', 0) > 0:
            monto_credito = Decimal(str(credito['monto_credito']))
            nueva_cita.monto_abono = (nueva_cita.monto_abono or Decimal('0')) + monto_credito
            nueva_cita.saldo_pendiente = (nueva_cita.monto_total or Decimal('0')) - nueva_cita.monto_abono
            if nueva_cita.saldo_pendiente <= 0:
                nueva_cita.saldo_pendiente = Decimal('0')
                nueva_cita.estado = 'confirmada'
            nueva_cita.notas = (
                f"Crédito de ${float(monto_credito):,.0f} aplicado "
                f"desde cita #{credito.get('codigo_origen', '')}."
            )
            db.session.commit()

        flash('¡Cita agendada exitosamente!', 'success')
        return redirect(url_for('citas.cita_confirmada', codigo=nueva_cita.codigo_reserva))
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
    servicio = db.session.get(Servicio, cita.id_servicio)
    empleado = db.session.get(Empleado, cita.id_empleado)

    return render_template('citas/confirmada.html', cita=cita, servicio=servicio, empleado=empleado)


@citas_bp.route('/citas/mis-citas')
def mis_citas():
    """Ver mis citas agendadas"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))

    # Obtener citas futuras — outerjoin para incluir citas sin especialista asignada aún
    citas_futuras = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).outerjoin(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).filter(
        Cita.id_cliente == session['usuario_id'],
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).order_by(Cita.fecha_hora_inicio).all()

    # Obtener citas pasadas — outerjoin por la misma razón
    citas_pasadas = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).outerjoin(
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

    cliente = db.session.get(Usuario, cita.id_cliente)
    servicio = db.session.get(Servicio, cita.id_servicio)

    # Verificar que no tenga ya un pago o no esté cancelada
    if cita.pago:
        flash('Esta cita ya tiene un pago registrado', 'error')
        return redirect(url_for('citas.mis_citas'))

    if cita.estado == 'cancelada':
        flash('No puedes pagar una cita cancelada', 'error')
        return redirect(url_for('citas.mis_citas'))

    form = PagoForm()
    if form.validate_on_submit():
        monto = form.monto.data
        metodo = form.metodo_pago.data
        referencia = form.referencia.data.strip() or None
        notas = form.notas.data.strip() or None

        # ── Tarea 2: Limitar monto al saldo pendiente real ─────────────────────
        saldo_real = float(cita.saldo_pendiente or cita.monto_total or 0)
        if float(monto) > saldo_real + 0.01:
            form.monto.errors.append(f'El monto no puede superar el saldo pendiente de ${saldo_real:,.0f}')
            return render_template('citas/cliente_pagos_form.html',
                                   cita=cita, cliente=cliente, servicio=servicio, form=form)

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

    # Inicializar valores predeterminados para GET o re-render en POST inválido
    if request.method == 'GET':
        form.monto.data = cita.saldo_pendiente or cita.monto_total
        form.metodo_pago.data = 'efectivo'

    return render_template('citas/cliente_pagos_form.html',
                           cita=cita, cliente=cliente,
                           servicio=servicio, form=form)


@citas_bp.route('/citas/descargar-pdf/<int:id_cita>')
def descargar_cita_pdf(id_cita):
    """Descargar comprobante PDF de una cita"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))

    cita = Cita.query.get_or_404(id_cita)
    # Verificar que la cita pertenece al usuario (o es admin)
    if session.get('tipo_usuario') not in ('admin', 'especialista'):
        if cita.id_cliente != session['usuario_id']:
            flash('No tienes permiso', 'error')
            return redirect(url_for('citas.mis_citas'))

    from flask import make_response
    from io import BytesIO
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        servicio = db.session.get(Servicio, cita.id_servicio)
        empleado = db.session.get(Empleado, cita.id_empleado) if cita.id_empleado else None
        cliente  = db.session.get(Usuario, cita.id_cliente)

        buffer = BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        title_style = ParagraphStyle('title', parent=styles['Title'],
                                     fontSize=22, textColor=colors.HexColor('#c41e3a'),
                                     spaceAfter=6)
        story.append(Paragraph('Rossmix — Salón de Belleza', title_style))
        story.append(Paragraph('Comprobante de Cita', styles['Heading2']))
        story.append(Spacer(1, 0.5*cm))

        data = [
            ['Campo', 'Detalle'],
            ['Código',     cita.codigo_reserva or '—'],
            ['Cliente',    cliente.nombre if cliente else '—'],
            ['Servicio',   servicio.nombre_servicio if servicio else '—'],
            ['Especialista', empleado.nombre if empleado else 'Por asignar'],
            ['Fecha',      cita.fecha_hora_inicio.strftime('%d/%m/%Y')],
            ['Hora',       cita.fecha_hora_inicio.strftime('%H:%M')],
            ['Estado',     cita.estado.replace('_', ' ').title()],
            ['Monto total', f"${float(cita.monto_total or 0):,.0f} COP"],
            ['Abono',       f"${float(cita.monto_abono or 0):,.0f} COP"],
            ['Saldo pendiente', f"${float(cita.saldo_pendiente or 0):,.0f} COP"],
        ]
        t = Table(data, colWidths=[5*cm, 12*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#c41e3a')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fff0f6')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#ffd6e8')),
            ('FONTSIZE',   (0,0), (-1,-1), 10),
            ('PADDING',    (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            'Gracias por elegir Rossmix. Recuerda cancelar con al menos 2 horas de anticipación.',
            styles['Italic']
        ))

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = (
            f'attachment; filename=rossmix_cita_{cita.codigo_reserva or id_cita}.pdf'
        )
        return response

    except ImportError:
        flash('ReportLab no está instalado. Instálalo con: pip install reportlab', 'error')
        return redirect(url_for('citas.mis_citas'))
    except Exception as e:
        flash(f'Error al generar PDF: {e}', 'error')
        return redirect(url_for('citas.mis_citas'))


@citas_bp.route('/citas/gestionar/<token>')
def gestionar_cita(token):
    """Vista de gestión de cita por token seguro"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))

    cita = Cita.query.filter_by(token_gestion=token).first_or_404()

    if cita.id_cliente != session['usuario_id']:
        flash('No tienes permiso para gestionar esta cita', 'error')
        return redirect(url_for('citas.mis_citas'))

    servicio = db.session.get(Servicio, cita.id_servicio)
    empleado = db.session.get(Empleado, cita.id_empleado) if cita.id_empleado else None

    # Determinar si aún se puede reprogramar/cancelar (≥2h de anticipación)
    puede_gestionar = (cita.fecha_hora_inicio - datetime.now()) >= timedelta(hours=2)
    puede_gestionar = puede_gestionar and cita.estado in ('confirmada', 'pendiente_pago')

    return render_template('citas/gestionar_cita.html',
                           cita=cita,
                           servicio=servicio,
                           empleado=empleado,
                           token=token,
                           puede_gestionar=puede_gestionar)


@citas_bp.route('/citas/reagendar-no-asistio/<int:id_cita>', methods=['POST'])
def reagendar_no_asistio(id_cita):
    """Reagendar cita con estado no_asistio — guarda el crédito en BD para evitar reutilización."""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    cita = Cita.query.filter_by(
        id_cita=id_cita, id_cliente=session['usuario_id'], estado='no_asistio'
    ).first_or_404()

    # Verificar que el crédito no fue ya consumido (notas actúa como flag en BD)
    if cita.notas and '[CREDITO_CONSUMIDO]' in cita.notas:
        flash('El crédito de esta cita ya fue utilizado.', 'error')
        return redirect(url_for('citas.mis_citas'))

    monto_credito = float(cita.monto_abono or 0)

    # Marcar el crédito como consumido en BD ANTES de guardarlo en sesión
    cita.notas = (cita.notas or '') + f' [CREDITO_CONSUMIDO:{cita.id_cita}]'
    db.session.commit()

    # Guardar el crédito en sesión (ahora está marcado en BD — no puede reutilizarse)
    session['credito_reagenda'] = {
        'id_cita_origen': cita.id_cita,
        'monto_credito': monto_credito,
        'codigo_origen': cita.codigo_reserva,
    }

    flash(
        f'Tienes un crédito de ${monto_credito:,.0f} '
        f'del abono de tu cita anterior (#{cita.codigo_reserva}). '
        f'Se descontará automáticamente al confirmar tu nueva cita.',
        'success'
    )
    return redirect(url_for('citas.agendar_paso1'))


@citas_bp.route('/citas/reprogramar/<int:id_cita>', methods=['GET'])
def reprogramar_cita_form(id_cita):
    """Formulario de reprogramación de cita"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))

    cita = Cita.query.filter_by(
        id_cita=id_cita, id_cliente=session['usuario_id']
    ).first_or_404()
    servicio = db.session.get(Servicio, cita.id_servicio)
    empleado = db.session.get(Empleado, cita.id_empleado) if cita.id_empleado else None

    hoy      = datetime.now().strftime('%Y-%m-%d')
    max_fecha = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

    form = SeleccionarHorarioForm(
        id_servicio=servicio.id_servicio if servicio else 0,
        id_empleado=empleado.id_empleado if empleado else 0,
    )

    return render_template('citas/paso3_fecha_hora.html',
                           servicio=servicio,
                           empleado=empleado,
                           hoy=hoy,
                           max_fecha=max_fecha,
                           form=form,
                           reprogramando=True,
                           id_cita_original=id_cita)


@citas_bp.route('/citas/reprogramar/<int:id_cita>', methods=['POST'])
def reprogramar_cita_submit(id_cita):
    """Procesa la reprogramación: cancela la cita original y crea una nueva."""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('auth.login'))

    cita_original = Cita.query.filter_by(
        id_cita=id_cita, id_cliente=session['usuario_id']
    ).first_or_404()

    # Solo se pueden reprogramar citas pendientes o confirmadas
    if cita_original.estado not in ('pendiente_pago', 'confirmada'):
        flash('Solo puedes reprogramar citas pendientes o confirmadas.', 'error')
        return redirect(url_for('citas.mis_citas'))

    # Mínimo 2 horas de anticipación para reprogramar
    if (cita_original.fecha_hora_inicio - datetime.now()) < timedelta(hours=2):
        flash('Debes reprogramar con al menos 2 horas de anticipación.', 'error')
        return redirect(url_for('citas.mis_citas'))

    form = SeleccionarHorarioForm()
    if not form.validate_on_submit():
        flash('Datos incompletos. Vuelve a seleccionar fecha y hora.', 'error')
        return redirect(url_for('citas.reprogramar_cita_form', id_cita=id_cita))

    id_servicio = int(form.id_servicio.data)
    id_empleado = int(form.id_empleado.data or 0)
    fecha_str   = form.fecha.data
    hora_str    = form.hora.data

    servicio = Servicio.query.get_or_404(id_servicio)

    try:
        fecha_hora_inicio = datetime.strptime(f'{fecha_str} {hora_str}', '%Y-%m-%d %H:%M')
        fecha_hora_fin    = fecha_hora_inicio + timedelta(minutes=servicio.duracion_minutos)
    except ValueError:
        flash('Fecha u hora inválida.', 'error')
        return redirect(url_for('citas.reprogramar_cita_form', id_cita=id_cita))

    if fecha_hora_inicio <= datetime.now():
        flash('La nueva fecha debe ser futura.', 'error')
        return redirect(url_for('citas.reprogramar_cita_form', id_cita=id_cita))

    if id_empleado == 0:
        ids = [e.id_empleado for e in EmpleadoServicio.query.filter_by(id_servicio=id_servicio).all()]
        if not ids:
            flash('No hay especialistas disponibles para ese servicio.', 'error')
            return redirect(url_for('citas.reprogramar_cita_form', id_cita=id_cita))
        id_empleado = random.choice(ids)

    if not CitaService.validar_disponibilidad_cita(id_empleado, fecha_hora_inicio, fecha_hora_fin):
        flash('El horario seleccionado ya no está disponible. Elige otro.', 'error')
        return redirect(url_for('citas.reprogramar_cita_form', id_cita=id_cita))

    try:
        # Guardar el abono de la cita original para transferirlo
        abono_previo = cita_original.monto_abono or Decimal('0')
        codigo_previo = cita_original.codigo_reserva

        # Cancelar la cita original
        cita_original.estado = 'cancelada'
        cita_original.notas = (
            (cita_original.notas or '') +
            f' [Reprogramada el {datetime.now().strftime("%d/%m/%Y %H:%M")}]'
        )
        db.session.commit()

        # Crear la nueva cita
        nueva_cita = CitaService.crear_cita(
            id_cliente=session['usuario_id'],
            id_servicio=id_servicio,
            id_empleado=id_empleado,
            fecha_hora_inicio=fecha_hora_inicio,
            fecha_hora_fin=fecha_hora_fin,
        )

        # Transferir el abono previo a la nueva cita
        if abono_previo > 0:
            nueva_cita.monto_abono     = abono_previo
            nueva_cita.saldo_pendiente = (nueva_cita.monto_total or Decimal('0')) - abono_previo
            if nueva_cita.saldo_pendiente <= 0:
                nueva_cita.saldo_pendiente = Decimal('0')
                nueva_cita.estado = 'confirmada'
            nueva_cita.notas = f'Reprogramación de cita #{codigo_previo}. Abono transferido.'
            db.session.commit()

        # Notificar al cliente
        try:
            add_notificacion(
                session['usuario_id'],
                'Cita reprogramada',
                f'Tu cita #{codigo_previo} fue reprogramada para el '
                f'{fecha_hora_inicio.strftime("%d/%m/%Y a las %H:%M")}. '
                f'Nuevo código: {nueva_cita.codigo_reserva}.',
                target=url_for('citas.mis_citas')
            )
        except Exception:
            pass

        flash('¡Cita reprogramada exitosamente!', 'success')
        return redirect(url_for('citas.cita_confirmada', codigo=nueva_cita.codigo_reserva))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al reprogramar la cita: {str(e)}', 'error')
        return redirect(url_for('citas.reprogramar_cita_form', id_cita=id_cita))

"""Portal de especialistas — ver citas disponibles y aceptarlas (Opción B)."""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.extensions import db
from app.models import Usuario, Empleado, Cita, Servicio, EmpleadoServicio
from app.utils.helpers import add_notificacion

especialista_bp = Blueprint('especialista', __name__, url_prefix='/especialista')


def _empleado_requerido():
    """Devuelve el Empleado vinculado a la sesión actual, o None."""
    if session.get('tipo_usuario') != 'especialista':
        return None
    usuario = Usuario.query.get(session.get('usuario_id'))
    if not usuario or not usuario.id_empleado:
        return None
    return Empleado.query.get(usuario.id_empleado)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@especialista_bp.route('/dashboard')
def dashboard():
    emp = _empleado_requerido()
    if not emp:
        flash('Acceso exclusivo para especialistas', 'error')
        return redirect(url_for('auth.login'))

    # Paso 8: Llamar a los métodos del modelo Empleado
    mis_citas = emp.citas_proximas
    disponibles = emp.obtener_citas_disponibles()
    agenda_hoy = emp.citas_hoy

    # Paso 9: Retornos — pasar resultados al template
    return render_template(
        'especialista/dashboard.html',
        empleado=emp,
        mis_citas=mis_citas,
        disponibles=disponibles,
        agenda_hoy=agenda_hoy,
        completadas_mes=emp.completadas_mes,
        ingresos_mes=emp.ingresos_mes
    )


# ── Citas disponibles ─────────────────────────────────────────────────────────

@especialista_bp.route('/citas-disponibles')
def citas_disponibles():
    emp = _empleado_requerido()
    if not emp:
        flash('Acceso exclusivo para especialistas', 'error')
        return redirect(url_for('auth.login'))

    # Paso 8: Usar método del modelo
    disponibles = emp.obtener_citas_disponibles()

    return render_template(
        'especialista/citas_disponibles.html',
        empleado=emp,
        disponibles=disponibles
    )


# ── Aceptar cita ──────────────────────────────────────────────────────────────

@especialista_bp.route('/aceptar-cita/<int:id_cita>', methods=['POST'])
def aceptar_cita(id_cita):
    emp = _empleado_requerido()
    if not emp:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403

    cita = Cita.query.get_or_404(id_cita)

    # Verificar que siga sin asignar
    if cita.id_empleado is not None:
        return jsonify({'success': False, 'message': 'Esta cita ya fue tomada por otra especialista'}), 409

    # Verificar que el servicio sea de mis especialidades
    mis_servicios = emp.obtener_servicios()
    if cita.id_servicio not in mis_servicios:
        return jsonify({'success': False, 'message': 'No realizas este servicio'}), 403

    try:
        cita.id_empleado = emp.id_empleado
        if cita.estado == 'pendiente_pago':
            cita.estado = 'confirmada'
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al asignar: {str(e)}'}), 500

    # Notificar al cliente
    try:
        add_notificacion(
            cita.id_cliente,
            '¡Especialista asignada!',
            f'{emp.nombre} ha aceptado tu cita del '
            f'{cita.fecha_hora_inicio.strftime("%d/%m/%Y a las %H:%M")}. '
            f'¡Tu cita está confirmada!'
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': f'Cita aceptada. Clienta notificada.',
        'especialista': emp.nombre
    })


# ── Cambiar estado de cita ────────────────────────────────────────────────────

@especialista_bp.route('/cambiar-estado/<int:id_cita>', methods=['POST'])
def cambiar_estado(id_cita):
    """Permite a la especialista avanzar el estado de su cita asignada."""
    emp = _empleado_requerido()
    if not emp:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403

    nuevo_estado = request.json.get('estado') if request.is_json else request.form.get('estado')
    if not nuevo_estado:
        return jsonify({'success': False, 'message': 'Estado no proporcionado'}), 400

    # Paso 8: Delegar la lógica al método de negocio del modelo
    resultado = emp.cambiar_estado_cita(id_cita, nuevo_estado)

    # Notificar al cliente si el cambio fue exitoso
    if resultado['success']:
        cita = Cita.query.get(id_cita)
        if cita and nuevo_estado == 'en_atencion':
            try:
                add_notificacion(
                    cita.id_cliente,
                    '💅 Tu cita ha comenzado',
                    f'{emp.nombre} ha iniciado la atención de tu servicio.'
                )
            except Exception:
                pass
        elif cita and nuevo_estado == 'completada':
            try:
                add_notificacion(
                    cita.id_cliente,
                    '✅ Servicio completado',
                    f'{emp.nombre} ha finalizado tu servicio. '
                    f'¡Esperamos que te haya encantado! 💖'
                )
            except Exception:
                pass

    status_code = 200 if resultado['success'] else 400
    return jsonify(resultado), status_code


# ── Mis citas ─────────────────────────────────────────────────────────────────

@especialista_bp.route('/mis-citas')
def mis_citas():
    emp = _empleado_requerido()
    if not emp:
        flash('Acceso exclusivo para especialistas', 'error')
        return redirect(url_for('auth.login'))

    # Paso 8: Usar propiedades del modelo
    proximas = emp.citas_proximas

    # Historial (pasadas) — query directa ya que no es frecuente
    pasadas = db.session.query(Cita, Usuario, Servicio)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .filter(
            Cita.id_empleado == emp.id_empleado,
            Cita.fecha_hora_inicio < datetime.now()
        ).order_by(Cita.fecha_hora_inicio.desc()).limit(20).all()

    return render_template(
        'especialista/mis_citas.html',
        empleado=emp,
        proximas=proximas,
        pasadas=pasadas
    )

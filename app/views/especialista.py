"""Portal de especialistas — ver citas disponibles y aceptarlas (Opción B)."""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.extensions import db
from app.models import Usuario, Empleado, Cita, Servicio, EmpleadoServicio
from app.utils.decorators import especialista_required
from app.utils.helpers import add_notificacion

especialista_bp = Blueprint('especialista', __name__, url_prefix='/especialista')


def _get_empleado():
    """Devuelve el Empleado vinculado a la sesión actual (ya validada por el decorador)."""
    usuario = db.session.get(Usuario, session['usuario_id'])
    return db.session.get(Empleado, usuario.id_empleado)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@especialista_bp.route('/dashboard')
@especialista_required
def dashboard():
    emp = _get_empleado()
    mis_citas   = emp.citas_proximas
    disponibles = emp.obtener_citas_disponibles()
    agenda_hoy  = emp.citas_hoy

    return render_template(
        'especialista/dashboard.html',
        empleado=emp,
        mis_citas=mis_citas,
        disponibles=disponibles,
        agenda_hoy=agenda_hoy,
        completadas_mes=emp.completadas_mes,
        ingresos_mes=emp.ingresos_mes,
    )


# ── Citas disponibles ─────────────────────────────────────────────────────────

@especialista_bp.route('/citas-disponibles')
@especialista_required
def citas_disponibles():
    emp = _get_empleado()
    disponibles = emp.obtener_citas_disponibles()
    return render_template(
        'especialista/citas_disponibles.html',
        empleado=emp,
        disponibles=disponibles,
    )


# ── Aceptar cita ──────────────────────────────────────────────────────────────

@especialista_bp.route('/aceptar-cita/<int:id_cita>', methods=['POST'])
@especialista_required
def aceptar_cita(id_cita):
    emp  = _get_empleado()
    cita = db.get_or_404(Cita, id_cita)

    if cita.id_empleado is not None:
        return jsonify({'success': False, 'message': 'Esta cita ya fue tomada por otra especialista'}), 409

    if cita.id_servicio not in emp.obtener_servicios():
        return jsonify({'success': False, 'message': 'No realizas este servicio'}), 403

    try:
        cita.id_empleado = emp.id_empleado
        if cita.estado == 'pendiente_pago':
            cita.estado = 'confirmada'
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al asignar: {str(e)}'}), 500

    try:
        add_notificacion(
            cita.id_cliente,
            '¡Especialista asignada!',
            f'{emp.nombre} ha aceptado tu cita del '
            f'{cita.fecha_hora_inicio.strftime("%d/%m/%Y a las %H:%M")}. '
            f'¡Tu cita está confirmada!',
        )
    except Exception:
        pass

    return jsonify({'success': True, 'message': 'Cita aceptada. Clienta notificada.', 'especialista': emp.nombre})


# ── Cambiar estado de cita ────────────────────────────────────────────────────

@especialista_bp.route('/cambiar-estado/<int:id_cita>', methods=['POST'])
@especialista_required
def cambiar_estado(id_cita):
    """Permite a la especialista avanzar el estado de su cita asignada."""
    emp = _get_empleado()
    nuevo_estado = request.json.get('estado') if request.is_json else request.form.get('estado')
    if not nuevo_estado:
        return jsonify({'success': False, 'message': 'Estado no proporcionado'}), 400

    resultado = emp.cambiar_estado_cita(id_cita, nuevo_estado)

    if resultado['success']:
        cita = db.session.get(Cita, id_cita)
        if cita and nuevo_estado == 'en_atencion':
            try:
                add_notificacion(
                    cita.id_cliente,
                    '💅 Tu cita ha comenzado',
                    f'{emp.nombre} ha iniciado la atención de tu servicio.',
                )
            except Exception:
                pass
        elif cita and nuevo_estado == 'completada':
            try:
                add_notificacion(
                    cita.id_cliente,
                    '✅ Servicio completado',
                    f'{emp.nombre} ha finalizado tu servicio. ¡Esperamos que te haya encantado! 💖',
                )
            except Exception:
                pass

    return jsonify(resultado), 200 if resultado['success'] else 400


# ── Mis citas ─────────────────────────────────────────────────────────────────

@especialista_bp.route('/mis-citas')
@especialista_required
def mis_citas():
    emp     = _get_empleado()
    proximas = emp.citas_proximas

    pasadas = db.session.query(Cita, Usuario, Servicio)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .filter(
            Cita.id_empleado == emp.id_empleado,
            Cita.fecha_hora_inicio < datetime.now(),
        ).order_by(Cita.fecha_hora_inicio.desc()).limit(20).all()

    return render_template(
        'especialista/mis_citas.html',
        empleado=emp,
        proximas=proximas,
        pasadas=pasadas,
    )

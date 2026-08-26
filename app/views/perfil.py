"""Panel de perfil editable para Admin, Cliente y Especialista."""
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import Usuario, Cita
from app.utils.decorators import login_required
from app.models.auditoria import registrar_auditoria

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')


def _stats_para_rol(usuario):
    """Devuelve estadísticas según el rol del usuario."""
    from datetime import datetime

    if usuario.tipo_usuario == 'cliente':
        total = Cita.query.filter_by(id_cliente=usuario.id).count()
        completadas = Cita.query.filter_by(id_cliente=usuario.id, estado='completada').count()
        pendientes  = Cita.query.filter(
            Cita.id_cliente == usuario.id,
            Cita.fecha_hora_inicio >= datetime.now(),
            Cita.estado.in_(['pendiente_pago', 'confirmada'])
        ).count()
        citas = completadas
        nivel = 'Bronce' if citas < 3 else ('Plata' if citas < 6 else 'Oro')
        return [
            {'valor': total,       'label': 'Total Citas'},
            {'valor': completadas, 'label': 'Completadas'},
            {'valor': pendientes,  'label': 'Próximas'},
            {'valor': nivel,       'label': 'Nivel'},
        ]

    elif usuario.tipo_usuario == 'especialista' and usuario.id_empleado:
        from app.models import Empleado
        emp = db.session.get(Empleado, usuario.id_empleado)
        if emp:
            total_asig = Cita.query.filter_by(id_empleado=emp.id_empleado).count()
            completadas = Cita.query.filter_by(id_empleado=emp.id_empleado, estado='completada').count()
            proximas = Cita.query.filter(
                Cita.id_empleado == emp.id_empleado,
                Cita.fecha_hora_inicio >= datetime.now(),
                Cita.estado.in_(['confirmada', 'pendiente_pago'])
            ).count()
            return [
                {'valor': total_asig,   'label': 'Citas Asignadas'},
                {'valor': completadas,  'label': 'Completadas'},
                {'valor': proximas,     'label': 'Próximas'},
            ]

    elif usuario.tipo_usuario == 'admin':
        from app.models import Empleado
        from sqlalchemy import func
        total_clientes  = Usuario.query.filter_by(tipo_usuario='cliente').count()
        total_citas     = Cita.query.count()
        total_empleados = Empleado.query.filter_by(activo=True).count()
        return [
            {'valor': total_clientes,  'label': 'Clientes'},
            {'valor': total_citas,     'label': 'Citas Total'},
            {'valor': total_empleados, 'label': 'Especialistas'},
        ]

    return []


@perfil_bp.route('/', methods=['GET', 'POST'])
@login_required
def mi_perfil():
    usuario = db.session.get(Usuario, session['usuario_id'])
    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        email    = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()

        # Validaciones
        errores = []
        if not nombre or len(nombre) < 3:
            errores.append('El nombre debe tener al menos 3 caracteres.')
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$', email):
            errores.append('El correo electrónico no es válido.')
        if not re.match(r'^\d{10}$', telefono):
            errores.append('El teléfono debe tener exactamente 10 dígitos.')
        # Email duplicado (otro usuario)
        existente = Usuario.query.filter(
            Usuario.email == email, Usuario.id != usuario.id
        ).first()
        if existente:
            errores.append('Este correo ya está registrado por otro usuario.')

        if errores:
            for e in errores:
                flash(e, 'error')
            return redirect(url_for('perfil.mi_perfil'))

        # Guardar cambios
        nombre_anterior = usuario.nombre
        usuario.nombre   = nombre
        usuario.email    = email
        usuario.telefono = telefono
        db.session.commit()

        # Actualizar sesión
        session['nombre'] = nombre
        session['email']  = email

        # Auditoría
        registrar_auditoria(
            accion='editar_perfil',
            id_usuario=usuario.id,
            id_actor=usuario.id,
            nombre=nombre,
            email=email,
            tipo_usuario=usuario.tipo_usuario,
            detalle=f'Usuario editó su propio perfil. Nombre anterior: {nombre_anterior}',
            ip_address=request.remote_addr,
        )
        db.session.commit()

        flash('¡Perfil actualizado correctamente!', 'success')
        return redirect(url_for('perfil.mi_perfil'))

    stats = _stats_para_rol(usuario)
    return render_template('perfil.html', usuario=usuario, stats=stats)


@perfil_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    usuario = db.session.get(Usuario, session['usuario_id'])
    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        actual     = request.form.get('password_actual', '')
        nueva      = request.form.get('password_nueva', '')
        confirmar  = request.form.get('password_confirmar', '')

        if not check_password_hash(usuario.password, actual):
            flash('La contraseña actual no es correcta.', 'error')
            return redirect(url_for('perfil.mi_perfil'))
        if len(nueva) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres.', 'error')
            return redirect(url_for('perfil.mi_perfil'))
        if nueva != confirmar:
            flash('Las contraseñas no coinciden.', 'error')
            return redirect(url_for('perfil.mi_perfil'))

        usuario.password = generate_password_hash(nueva)
        db.session.commit()

        registrar_auditoria(
            accion='cambio_password',
            id_usuario=usuario.id,
            id_actor=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            tipo_usuario=usuario.tipo_usuario,
            detalle='Usuario cambió su propia contraseña',
            ip_address=request.remote_addr,
        )
        db.session.commit()

        flash('¡Contraseña actualizada correctamente!', 'success')

    return redirect(url_for('perfil.mi_perfil'))

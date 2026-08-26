"""Gestión de cuentas de especialista (admin)."""
from flask import render_template, request, jsonify, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Usuario, Empleado
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/especialistas')
@admin_required
def especialistas():
    """Listar cuentas de especialista"""
    cuentas = Usuario.query.filter_by(tipo_usuario='especialista').order_by(Usuario.nombre).all()
    empleados_sin_cuenta = Empleado.query.filter(
        Empleado.activo == True,
        ~Empleado.id_empleado.in_(
            db.session.query(Usuario.id_empleado).filter(
                Usuario.tipo_usuario == 'especialista',
                Usuario.id_empleado.isnot(None)
            )
        )
    ).all()
    return render_template('admin/especialistas.html',
                           cuentas=cuentas,
                           empleados_sin_cuenta=empleados_sin_cuenta)


@admin_bp.route('/especialistas/crear', methods=['POST'])
@admin_required
def especialistas_crear():
    """Crear cuenta de acceso para una especialista"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    id_empleado = request.form.get('id_empleado', type=int)
    email       = request.form.get('email', '').strip()
    password    = request.form.get('password', '').strip()

    if not all([id_empleado, email, password]):
        msg = 'Todos los campos son obligatorios'
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('admin.especialistas'))

    empleado = db.get_or_404(Empleado, id_empleado)

    if Usuario.query.filter_by(email=email).first():
        msg = f'El email {email} ya está registrado'
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('admin.especialistas'))

    nuevo = Usuario(
        nombre=empleado.nombre,
        email=email,
        telefono='0000000000',
        password=generate_password_hash(password),
        tipo_usuario='especialista',
        id_empleado=id_empleado
    )
    db.session.add(nuevo)
    db.session.commit()

    if is_ajax:
        return jsonify({
            'success': True,
            'message': f'Cuenta creada para {empleado.nombre}',
            'cuenta': {'id': nuevo.id, 'nombre': nuevo.nombre, 'email': nuevo.email}
        })
    flash(f'Cuenta creada para {empleado.nombre}', 'success')
    return redirect(url_for('admin.especialistas'))


@admin_bp.route('/especialistas/eliminar/<int:id_usuario>', methods=['POST'])
@admin_required
def especialistas_eliminar(id_usuario):
    """Eliminar cuenta de especialista"""
    usuario = db.get_or_404(Usuario, id_usuario)
    if usuario.tipo_usuario != 'especialista':
        return jsonify({'success': False, 'message': 'No es una cuenta de especialista'}), 400
    nombre = usuario.nombre
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Cuenta de {nombre} eliminada'})


@admin_bp.route('/especialistas/reset-password/<int:id_usuario>', methods=['POST'])
@admin_required
def especialistas_reset_password(id_usuario):
    """Resetear contraseña de especialista"""
    usuario = db.get_or_404(Usuario, id_usuario)
    nueva = request.form.get('nueva_password', '').strip()
    if len(nueva) < 6:
        return jsonify({'success': False, 'message': 'Mínimo 6 caracteres'}), 400
    usuario.password = generate_password_hash(nueva)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Contraseña actualizada'})

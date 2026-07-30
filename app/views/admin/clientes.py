"""CRUD de clientes (admin)."""
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Usuario, Cita
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/clientes')
@admin_required
def clientes():
    """Listar todos los clientes"""
    lista = Usuario.query.filter_by(tipo_usuario='cliente').order_by(Usuario.nombre).all()
    # Añadir conteo de citas canceladas por cliente
    for c in lista:
        try:
            c.citas_canceladas = Cita.query.filter_by(id_cliente=c.id, estado='cancelada').count()
        except Exception:
            c.citas_canceladas = 0
    return render_template('admin/clientes.html', clientes=lista, filter_label='Todos')


@admin_bp.route('/clientes/hoy')
@admin_required
def clientes_hoy():
    """Listar clientes registrados hoy"""
    from sqlalchemy import func

    hoy = datetime.now().date()
    lista = Usuario.query.filter(
        Usuario.tipo_usuario == 'cliente',
        func.date(Usuario.fecha_registro) == hoy
    ).order_by(Usuario.nombre).all()

    return render_template(
        'admin/clientes.html',
        clientes=lista,
        view_title='Clientes registrados hoy',
        filter_label='Hoy'
    )


@admin_bp.route('/clientes/editar/<int:id_cliente>', methods=['GET', 'POST'])
@admin_required
def clientes_editar(id_cliente):
    """Editar cliente"""
    cliente = Usuario.query.get_or_404(id_cliente)

    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.email = request.form.get('email')
        cliente.telefono = request.form.get('telefono')
        cliente.activo = request.form.get('activo') == 'on'

        # Cambiar contraseña solo si se proporciona una nueva
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            cliente.password = generate_password_hash(nueva_password)

        db.session.commit()
        flash(f'Cliente {cliente.nombre} actualizado exitosamente', 'success')
        return redirect(url_for('admin.clientes'))

    return render_template('admin/clientes_form.html', cliente=cliente)


@admin_bp.route('/clientes/eliminar/<int:id_cliente>', methods=['POST'])
@admin_required
def clientes_eliminar(id_cliente):
    """Eliminar cliente"""
    cliente = Usuario.query.get_or_404(id_cliente)

    # Verificar si tiene citas futuras
    citas_futuras = Cita.query.filter(
        Cita.id_cliente == id_cliente,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    if citas_futuras > 0:
        return jsonify({
            'success': False,
            'message': f'No se puede eliminar. El cliente tiene {citas_futuras} cita(s) pendiente(s)'
        }), 400

    nombre = cliente.nombre
    db.session.delete(cliente)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Cliente {nombre} eliminado exitosamente'
    })

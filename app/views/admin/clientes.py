"""CRUD de clientes (admin)."""
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Usuario, Cita
from app.utils.decorators import admin_required
from app.views.admin import admin_bp
from app.models.auditoria import registrar_auditoria


def _obtener_clientes():
    """Obtiene todos los registros de cliente, tolerando formato heredado."""
    from sqlalchemy import func

    clientes = Usuario.query.filter(
        func.lower(func.trim(Usuario.tipo_usuario)) == 'cliente'
    ).order_by(Usuario.nombre).all()

    for cliente in clientes:
        cliente.citas_canceladas = Cita.query.filter_by(
            id_cliente=cliente.id,
            estado='cancelada'
        ).count()

    return clientes


@admin_bp.route('/clientes')
@admin_required
def clientes():
    """Listar todos los clientes"""
    lista = _obtener_clientes()
    return render_template('admin/clientes.html', clientes=lista, filter_label='Todos')


@admin_bp.route('/clientes/datos/<int:id_cliente>', methods=['GET'])
@admin_required
def clientes_datos(id_cliente):
    """Retorna datos del cliente para modal AJAX"""
    cliente = Usuario.query.get_or_404(id_cliente)
    return jsonify({
        'id': cliente.id,
        'nombre': cliente.nombre,
        'email': cliente.email,
        'telefono': cliente.telefono or '',
        'activo': cliente.activo,
        'fecha_registro': cliente.fecha_registro.strftime('%d/%m/%Y a las %H:%M') if cliente.fecha_registro else 'N/A',
        'total_citas': len(cliente.citas)
    })


@admin_bp.route('/clientes/hoy')
@admin_required
def clientes_hoy():
    """Listar clientes registrados hoy"""
    hoy = datetime.now().date()
    lista = _obtener_clientes()
    lista = [
        cliente for cliente in lista
        if cliente.fecha_registro and cliente.fecha_registro.date() == hoy
    ]

    return render_template(
        'admin/clientes.html',
        clientes=lista,
        view_title='Clientes registrados hoy',
        filter_label='Hoy'
    )


@admin_bp.route('/clientes/editar/<int:id_cliente>', methods=['GET', 'POST'])
@admin_required
def clientes_editar(id_cliente):
    """Editar cliente — soporta JSON (modal) y form normal"""
    cliente = Usuario.query.get_or_404(id_cliente)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre', '').strip()
        cliente.email = request.form.get('email', '').strip()
        cliente.telefono = request.form.get('telefono', '').strip()
        cliente.activo = request.form.get('activo') == 'on'

        nueva_password = request.form.get('nueva_password', '').strip()
        if nueva_password:
            cliente.password = generate_password_hash(nueva_password)

        db.session.commit()

        registrar_auditoria(
            accion='editar',
            id_usuario=cliente.id,
            id_actor=session.get('usuario_id'),
            nombre=cliente.nombre,
            email=cliente.email,
            telefono=cliente.telefono,
            tipo_usuario=cliente.tipo_usuario,
            detalle='Admin editó datos del cliente',
            ip_address=request.remote_addr,
        )
        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'message': f'Cliente {cliente.nombre} actualizado exitosamente',
                'cliente': {
                    'id': cliente.id,
                    'nombre': cliente.nombre,
                    'email': cliente.email,
                    'telefono': cliente.telefono or '—',
                    'activo': cliente.activo
                }
            })
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

    nombre        = cliente.nombre
    email_cliente = cliente.email or ''
    db.session.delete(cliente)
    db.session.commit()

    registrar_auditoria(
        accion='eliminar',
        id_usuario=None,
        id_actor=session.get('usuario_id'),
        nombre=nombre,
        email=email_cliente,
        detalle=f'Admin eliminó al cliente {nombre}',
        ip_address=request.remote_addr,
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Cliente {nombre} eliminado exitosamente'
    })

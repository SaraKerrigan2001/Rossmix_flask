"""CRUD de servicios (admin)."""
from datetime import datetime
from decimal import Decimal
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import Servicio, Cita
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/servicios')
@admin_required
def servicios():
    """Listar todos los servicios"""
    lista = Servicio.query.order_by(Servicio.nombre_servicio).all()
    return render_template('admin/servicios.html', servicios=lista)


@admin_bp.route('/servicios/crear', methods=['GET', 'POST'])
@admin_required
def servicios_crear():
    """Crear nuevo servicio"""
    if request.method == 'POST':
        nombre = request.form.get('nombre_servicio')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio_total')
        duracion = request.form.get('duracion_minutos')

        if not all([nombre, precio, duracion]):
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('admin.servicios_crear'))

        # Crear servicio
        nuevo_servicio = Servicio(
            nombre_servicio=nombre,
            descripcion=descripcion,
            precio_total=Decimal(precio),
            duracion_minutos=int(duracion),
            activo=True
        )

        db.session.add(nuevo_servicio)
        db.session.commit()

        flash(f'Servicio {nombre} creado exitosamente', 'success')
        return redirect(url_for('admin.servicios'))

    return render_template('admin/servicios_form.html', servicio=None)


@admin_bp.route('/servicios/editar/<int:id_servicio>', methods=['GET', 'POST'])
@admin_required
def servicios_editar(id_servicio):
    """Editar servicio existente"""
    servicio = Servicio.query.get_or_404(id_servicio)

    if request.method == 'POST':
        servicio.nombre_servicio = request.form.get('nombre_servicio')
        servicio.descripcion = request.form.get('descripcion')
        servicio.precio_total = Decimal(request.form.get('precio_total'))
        servicio.duracion_minutos = int(request.form.get('duracion_minutos'))
        servicio.activo = request.form.get('activo') == 'on'

        db.session.commit()
        flash(f'Servicio {servicio.nombre_servicio} actualizado exitosamente', 'success')
        return redirect(url_for('admin.servicios'))

    return render_template('admin/servicios_form.html', servicio=servicio)


@admin_bp.route('/servicios/eliminar/<int:id_servicio>', methods=['POST'])
@admin_required
def servicios_eliminar(id_servicio):
    """Eliminar servicio"""
    servicio = Servicio.query.get_or_404(id_servicio)

    # Verificar si tiene citas futuras
    citas_futuras = Cita.query.filter(
        Cita.id_servicio == id_servicio,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    if citas_futuras > 0:
        return jsonify({
            'success': False,
            'message': f'No se puede eliminar. El servicio tiene {citas_futuras} cita(s) pendiente(s)'
        }), 400

    nombre = servicio.nombre_servicio
    db.session.delete(servicio)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Servicio {nombre} eliminado exitosamente'
    })

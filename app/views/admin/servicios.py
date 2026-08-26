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


@admin_bp.route('/servicios/datos/<int:id_servicio>', methods=['GET'])
@admin_required
def servicios_datos(id_servicio):
    """Retorna datos del servicio para modal AJAX"""
    svc = db.get_or_404(Servicio, id_servicio)
    return jsonify({
        'id_servicio': svc.id_servicio,
        'nombre_servicio': svc.nombre_servicio,
        'descripcion': svc.descripcion or '',
        'precio_total': float(svc.precio_total),
        'duracion_minutos': svc.duracion_minutos,
        'activo': svc.activo
    })


@admin_bp.route('/servicios/crear', methods=['GET', 'POST'])
@admin_required
def servicios_crear():
    """Crear nuevo servicio — soporta JSON (modal) y form normal"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        nombre = request.form.get('nombre_servicio', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio = request.form.get('precio_total', '').strip()
        duracion = request.form.get('duracion_minutos', '').strip()

        if not all([nombre, precio, duracion]):
            if is_ajax:
                return jsonify({'success': False, 'message': 'Nombre, precio y duración son obligatorios'}), 400
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('admin.servicios_crear'))

        nuevo_servicio = Servicio(
            nombre_servicio=nombre,
            descripcion=descripcion or None,
            precio_total=Decimal(precio),
            duracion_minutos=int(duracion),
            activo=True
        )
        db.session.add(nuevo_servicio)
        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'message': f'Servicio {nombre} creado exitosamente',
                'servicio': {
                    'id_servicio': nuevo_servicio.id_servicio,
                    'nombre_servicio': nuevo_servicio.nombre_servicio,
                    'descripcion': nuevo_servicio.descripcion or '—',
                    'precio_total': float(nuevo_servicio.precio_total),
                    'duracion_minutos': nuevo_servicio.duracion_minutos,
                    'activo': nuevo_servicio.activo
                }
            })
        flash(f'Servicio {nombre} creado exitosamente', 'success')
        return redirect(url_for('admin.servicios'))

    return render_template('admin/servicios_form.html', servicio=None)


@admin_bp.route('/servicios/editar/<int:id_servicio>', methods=['GET', 'POST'])
@admin_required
def servicios_editar(id_servicio):
    """Editar servicio existente — soporta JSON (modal) y form normal"""
    servicio = db.get_or_404(Servicio, id_servicio)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        servicio.nombre_servicio = request.form.get('nombre_servicio', '').strip()
        servicio.descripcion = request.form.get('descripcion', '').strip() or None
        servicio.precio_total = Decimal(request.form.get('precio_total'))
        servicio.duracion_minutos = int(request.form.get('duracion_minutos'))
        servicio.activo = request.form.get('activo') == 'on'

        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'message': f'Servicio {servicio.nombre_servicio} actualizado exitosamente',
                'servicio': {
                    'id_servicio': servicio.id_servicio,
                    'nombre_servicio': servicio.nombre_servicio,
                    'descripcion': servicio.descripcion or '—',
                    'precio_total': float(servicio.precio_total),
                    'duracion_minutos': servicio.duracion_minutos,
                    'activo': servicio.activo
                }
            })
        flash(f'Servicio {servicio.nombre_servicio} actualizado exitosamente', 'success')
        return redirect(url_for('admin.servicios'))

    return render_template('admin/servicios_form.html', servicio=servicio)


@admin_bp.route('/servicios/eliminar/<int:id_servicio>', methods=['POST'])
@admin_required
def servicios_eliminar(id_servicio):
    """Eliminar servicio"""
    servicio = db.get_or_404(Servicio, id_servicio)

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

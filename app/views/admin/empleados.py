"""CRUD de empleados (admin)."""
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import Empleado, Servicio, EmpleadoServicio, Cita
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/empleados')
@admin_required
def empleados():
    """Listar todos los empleados"""
    lista = Empleado.query.order_by(Empleado.nombre).all()
    servicios = Servicio.query.filter_by(activo=True).all()
    return render_template('admin/empleados.html', empleados=lista, servicios=servicios)


@admin_bp.route('/empleados/datos/<int:id_empleado>', methods=['GET'])
@admin_required
def empleados_datos(id_empleado):
    """Retorna datos del empleado para modal AJAX"""
    empleado = Empleado.query.get_or_404(id_empleado)
    servicios_empleado = [es.id_servicio for es in EmpleadoServicio.query.filter_by(id_empleado=id_empleado).all()]
    return jsonify({
        'id_empleado': empleado.id_empleado,
        'nombre': empleado.nombre,
        'especialidad': empleado.especialidad or '',
        'activo': empleado.activo,
        'servicios_empleado': servicios_empleado
    })


@admin_bp.route('/empleados/crear', methods=['GET', 'POST'])
@admin_required
def empleados_crear():
    """Crear nuevo empleado — soporta JSON (modal) y form normal"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        especialidad = request.form.get('especialidad', '').strip()
        servicios_ids = request.form.getlist('servicios')

        if not nombre:
            if is_ajax:
                return jsonify({'success': False, 'message': 'El nombre es obligatorio'}), 400
            flash('El nombre es obligatorio', 'error')
            return redirect(url_for('admin.empleados_crear'))

        nuevo_empleado = Empleado(
            nombre=nombre,
            especialidad=especialidad or None,
            activo=True
        )
        db.session.add(nuevo_empleado)
        db.session.flush()

        for id_servicio in servicios_ids:
            db.session.add(EmpleadoServicio(
                id_empleado=nuevo_empleado.id_empleado,
                id_servicio=int(id_servicio)
            ))

        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'message': f'Empleado {nombre} creado exitosamente',
                'empleado': {
                    'id_empleado': nuevo_empleado.id_empleado,
                    'nombre': nuevo_empleado.nombre,
                    'especialidad': nuevo_empleado.especialidad or '—',
                    'activo': nuevo_empleado.activo,
                    'servicios_count': len(servicios_ids),
                    'fecha_registro': nuevo_empleado.fecha_registro.strftime('%d/%m/%Y') if nuevo_empleado.fecha_registro else '—'
                }
            })
        flash(f'Empleado {nombre} creado exitosamente', 'success')
        return redirect(url_for('admin.empleados'))

    servicios = Servicio.query.filter_by(activo=True).all()
    return render_template('admin/empleados_form.html', empleado=None, servicios=servicios)


@admin_bp.route('/empleados/editar/<int:id_empleado>', methods=['GET', 'POST'])
@admin_required
def empleados_editar(id_empleado):
    """Editar empleado existente — soporta JSON (modal) y form normal"""
    empleado = Empleado.query.get_or_404(id_empleado)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        empleado.nombre = request.form.get('nombre', '').strip()
        empleado.especialidad = request.form.get('especialidad', '').strip() or None
        empleado.activo = request.form.get('activo') == 'on'

        servicios_ids = request.form.getlist('servicios')
        EmpleadoServicio.query.filter_by(id_empleado=id_empleado).delete()

        for id_servicio in servicios_ids:
            db.session.add(EmpleadoServicio(
                id_empleado=id_empleado,
                id_servicio=int(id_servicio)
            ))

        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'message': f'Empleado {empleado.nombre} actualizado exitosamente',
                'empleado': {
                    'id_empleado': empleado.id_empleado,
                    'nombre': empleado.nombre,
                    'especialidad': empleado.especialidad or '—',
                    'activo': empleado.activo,
                    'servicios_count': len(servicios_ids),
                    'fecha_registro': empleado.fecha_registro.strftime('%d/%m/%Y') if empleado.fecha_registro else '—'
                }
            })
        flash(f'Empleado {empleado.nombre} actualizado exitosamente', 'success')
        return redirect(url_for('admin.empleados'))

    servicios = Servicio.query.filter_by(activo=True).all()
    servicios_empleado = [es.id_servicio for es in EmpleadoServicio.query.filter_by(id_empleado=id_empleado).all()]
    return render_template('admin/empleados_form.html',
                           empleado=empleado,
                           servicios=servicios,
                           servicios_empleado=servicios_empleado)


@admin_bp.route('/empleados/eliminar/<int:id_empleado>', methods=['POST'])
@admin_required
def empleados_eliminar(id_empleado):
    """Eliminar empleado"""
    empleado = Empleado.query.get_or_404(id_empleado)

    # Verificar si tiene citas futuras
    citas_futuras = Cita.query.filter(
        Cita.id_empleado == id_empleado,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    if citas_futuras > 0:
        return jsonify({
            'success': False,
            'message': f'No se puede eliminar. El empleado tiene {citas_futuras} cita(s) pendiente(s)'
        }), 400

    nombre = empleado.nombre
    db.session.delete(empleado)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Empleado {nombre} eliminado exitosamente'
    })

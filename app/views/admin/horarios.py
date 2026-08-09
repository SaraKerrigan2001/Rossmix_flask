"""CRUD de horarios (admin)."""
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import Empleado, HorarioEmpleado
from app.utils.decorators import admin_required
from app.views.admin import admin_bp

DIAS_SEMANA = {
    0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
    4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
}


@admin_bp.route('/horarios')
@admin_required
def horarios():
    """Listar horarios de todos los empleados"""
    empleados_list = Empleado.query.filter_by(activo=True).all()
    return render_template('admin/horarios.html', empleados=empleados_list, dias_semana=DIAS_SEMANA)


@admin_bp.route('/horarios/crear/<int:id_empleado>', methods=['GET', 'POST'])
@admin_required
def horarios_crear(id_empleado):
    """Crear horario para empleado — soporta JSON (modal) y form normal"""
    empleado = Empleado.query.get_or_404(id_empleado)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        dia_semana = int(request.form.get('dia_semana'))
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fin_str = request.form.get('hora_fin')

        horario_existente = HorarioEmpleado.query.filter_by(
            id_empleado=id_empleado,
            dia_semana=dia_semana
        ).first()

        if horario_existente:
            msg = 'Ya existe un horario para este empleado en ese día'
            if is_ajax:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'error')
            return redirect(url_for('admin.horarios_crear', id_empleado=id_empleado))

        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        if hora_inicio >= hora_fin:
            msg = 'La hora de inicio debe ser menor que la hora de fin'
            if is_ajax:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'error')
            return redirect(url_for('admin.horarios_crear', id_empleado=id_empleado))

        nuevo_horario = HorarioEmpleado(
            id_empleado=id_empleado,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )
        db.session.add(nuevo_horario)
        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'message': f'Horario creado para {empleado.nombre}',
                'horario': {
                    'id_horario': nuevo_horario.id_horario,
                    'dia_semana': dia_semana,
                    'dia_nombre': DIAS_SEMANA[dia_semana],
                    'hora_inicio': hora_inicio_str,
                    'hora_fin': hora_fin_str,
                    'id_empleado': id_empleado
                }
            })
        flash(f'Horario creado exitosamente para {empleado.nombre}', 'success')
        return redirect(url_for('admin.horarios'))

    return render_template('admin/horarios_form.html', empleado=empleado, horario=None, dias_semana=DIAS_SEMANA)


@admin_bp.route('/horarios/editar/<int:id_horario>', methods=['GET', 'POST'])
@admin_required
def horarios_editar(id_horario):
    """Editar horario — soporta JSON (modal) y form normal"""
    horario = HorarioEmpleado.query.get_or_404(id_horario)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fin_str = request.form.get('hora_fin')

        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        if hora_inicio >= hora_fin:
            msg = 'La hora de inicio debe ser menor que la hora de fin'
            if is_ajax:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'error')
            return redirect(url_for('admin.horarios_editar', id_horario=id_horario))

        horario.hora_inicio = hora_inicio
        horario.hora_fin = hora_fin
        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'message': 'Horario actualizado exitosamente',
                'horario': {
                    'id_horario': horario.id_horario,
                    'hora_inicio': hora_inicio_str,
                    'hora_fin': hora_fin_str,
                }
            })
        flash('Horario actualizado exitosamente', 'success')
        return redirect(url_for('admin.horarios'))

    return render_template(
        'admin/horarios_form.html',
        empleado=horario.empleado,
        horario=horario,
        dias_semana=DIAS_SEMANA)


@admin_bp.route('/horarios/eliminar/<int:id_horario>', methods=['POST'])
@admin_required
def horarios_eliminar(id_horario):
    """Eliminar horario"""
    horario = HorarioEmpleado.query.get_or_404(id_horario)

    db.session.delete(horario)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Horario eliminado exitosamente'
    })

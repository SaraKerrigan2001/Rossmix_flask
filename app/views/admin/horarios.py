"""CRUD de horarios (admin)."""
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import Empleado, HorarioEmpleado
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/horarios')
@admin_required
def horarios():
    """Listar horarios de todos los empleados"""
    empleados_list = Empleado.query.filter_by(activo=True).all()
    dias_semana = {
        0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
        4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
    }
    return render_template('admin/horarios.html', empleados=empleados_list, dias_semana=dias_semana)


@admin_bp.route('/horarios/crear/<int:id_empleado>', methods=['GET', 'POST'])
@admin_required
def horarios_crear(id_empleado):
    """Crear horario para empleado"""
    empleado = Empleado.query.get_or_404(id_empleado)

    if request.method == 'POST':
        dia_semana = int(request.form.get('dia_semana'))
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fin_str = request.form.get('hora_fin')

        # Validar que no exista ya un horario para ese día
        horario_existente = HorarioEmpleado.query.filter_by(
            id_empleado=id_empleado,
            dia_semana=dia_semana
        ).first()

        if horario_existente:
            flash('Ya existe un horario para este empleado en ese día', 'error')
            return redirect(url_for('admin.horarios_crear', id_empleado=id_empleado))

        # Convertir strings a time
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        if hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser menor que la hora de fin', 'error')
            return redirect(url_for('admin.horarios_crear', id_empleado=id_empleado))

        # Crear horario
        nuevo_horario = HorarioEmpleado(
            id_empleado=id_empleado,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )

        db.session.add(nuevo_horario)
        db.session.commit()

        flash(f'Horario creado exitosamente para {empleado.nombre}', 'success')
        return redirect(url_for('admin.horarios'))

    # GET
    dias_semana = {
        0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
        4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
    }
    return render_template('admin/horarios_form.html', empleado=empleado, horario=None, dias_semana=dias_semana)


@admin_bp.route('/horarios/editar/<int:id_horario>', methods=['GET', 'POST'])
@admin_required
def horarios_editar(id_horario):
    """Editar horario"""
    horario = HorarioEmpleado.query.get_or_404(id_horario)

    if request.method == 'POST':
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fin_str = request.form.get('hora_fin')

        # Convertir strings a time
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        if hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser menor que la hora de fin', 'error')
            return redirect(url_for('admin.horarios_editar', id_horario=id_horario))

        horario.hora_inicio = hora_inicio
        horario.hora_fin = hora_fin

        db.session.commit()
        flash('Horario actualizado exitosamente', 'success')
        return redirect(url_for('admin.horarios'))

    # GET
    dias_semana = {
        0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
        4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
    }
    return render_template(
        'admin/horarios_form.html',
        empleado=horario.empleado,
        horario=horario,
        dias_semana=dias_semana)


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

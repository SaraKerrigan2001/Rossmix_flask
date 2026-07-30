"""Exportación a Excel de datos de citas y pagos."""
import io
import openpyxl
from datetime import datetime, timedelta
from flask import send_file, flash, redirect, url_for
from app.models import Cita, Pago, Usuario, Servicio, HorarioEmpleado
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/exportar/<tipo>/<periodo>')
@admin_required
def exportar_excel(tipo, periodo):
    """
    Exporta datos de citas, pagos, empleados, etc. a Excel.
    tipo: 'citas', 'pagos', 'empleados', 'servicios', 'clientes', 'horarios'
    periodo: 'diario', 'semana', 'mes', 'ano'
    """
    if tipo not in ['citas', 'pagos', 'empleados', 'servicios', 'clientes', 'horarios']:
        flash('Tipo de exportación no válido.', 'error')
        return redirect(url_for('admin.dashboard'))

    hoy = datetime.now()
    if periodo == 'diario':
        fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'ano':
        fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        fecha_inicio = datetime(1900, 1, 1)

    wb = openpyxl.Workbook()
    ws = wb.active

    if tipo == 'citas':
        ws.title = "Citas"
        ws.append(["ID", "Código", "Cliente", "Servicio", "Monto", "Estado", "Fecha"])
        query = Cita.query.filter(Cita.fecha_creacion >= fecha_inicio).all()
        for c in query:
            cli = Usuario.query.get(c.id_cliente)
            srv = Servicio.query.get(c.id_servicio)
            ws.append([c.id_cita, c.codigo_reserva, cli.nombre if cli else '', srv.nombre_servicio if srv else '', float(c.monto_total), c.estado, c.fecha_creacion.strftime('%Y-%m-%d %H:%M')])
            
    elif tipo == 'pagos':
        ws.title = "Pagos"
        ws.append(["ID Pago", "Código Cita", "Monto", "Método", "Estado", "Fecha"])
        query = Pago.query.filter(Pago.fecha_pago >= fecha_inicio).all()
        for p in query:
            cita = Cita.query.get(p.id_cita)
            ws.append([p.id_pago, cita.codigo_reserva if cita else '', float(p.monto), p.metodo_pago, p.estado_pago, p.fecha_pago.strftime('%Y-%m-%d %H:%M')])
            
    elif tipo == 'empleados':
        ws.title = "Empleados"
        ws.append(["ID", "Nombre", "Email", "Especialidad", "Estado"])
        query = Usuario.query.filter_by(tipo_usuario='empleado').filter(Usuario.fecha_registro >= fecha_inicio).all()
        for e in query:
            ws.append([e.id, e.nombre, e.email, getattr(e, 'especialidad', ''), "Activo" if getattr(e, 'activo', True) else "Inactivo"])
            
    elif tipo == 'clientes':
        ws.title = "Clientes"
        ws.append(["ID", "Nombre", "Email", "Teléfono", "Fecha Registro"])
        query = Usuario.query.filter_by(tipo_usuario='cliente').filter(Usuario.fecha_registro >= fecha_inicio).all()
        for c in query:
            ws.append([c.id, c.nombre, c.email, c.telefono, c.fecha_registro.strftime('%Y-%m-%d %H:%M')])
            
    elif tipo == 'servicios':
        ws.title = "Servicios"
        ws.append(["ID", "Nombre", "Descripción", "Precio", "Duración"])
        query = Servicio.query.all() # No date filter for services
        for s in query:
            ws.append([s.id_servicio, s.nombre_servicio, s.descripcion, float(s.precio_total), s.duracion_minutos])
            
    elif tipo == 'horarios':
        ws.title = "Horarios"
        ws.append(["ID Horario", "Empleado", "Día", "Hora Inicio", "Hora Fin"])
        query = HorarioEmpleado.query.all()
        for h in query:
            emp = Usuario.query.get(h.id_empleado)
            ws.append([h.id_horario, emp.nombre if emp else '', h.dia_semana, h.hora_inicio.strftime('%H:%M'), h.hora_fin.strftime('%H:%M')])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"export_{tipo}_{periodo}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

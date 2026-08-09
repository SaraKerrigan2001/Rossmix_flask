"""Dashboard de administrador."""
from datetime import datetime
from sqlalchemy import func
from flask import render_template
from app.extensions import db
from app.models import Usuario, Empleado, Cita
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/')
@admin_required
def dashboard():
    """Dashboard principal de administrador con estadísticas"""
    from dateutil.relativedelta import relativedelta
    
    # Citas de hoy
    hoy = datetime.now().date()
    citas_hoy = Cita.query.filter(
        func.date(Cita.fecha_hora_inicio) == hoy,
        Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion'])
    ).count()

    # Total clientes
    total_clientes = Usuario.query.filter_by(tipo_usuario='cliente', activo=True).count()

    # Empleados activos
    empleados_activos = Empleado.query.filter_by(activo=True).count()

    # Ingresos del mes
    primer_dia_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ingresos_mes = db.session.query(func.sum(Cita.monto_total)).filter(
        Cita.fecha_hora_inicio >= primer_dia_mes,
        Cita.estado.in_(['completada', 'confirmada'])
    ).scalar() or 0

    # Ingresos mes anterior
    primer_dia_mes_anterior = primer_dia_mes - relativedelta(months=1)
    ingresos_mes_anterior = db.session.query(func.sum(Cita.monto_total)).filter(
        Cita.fecha_hora_inicio >= primer_dia_mes_anterior,
        Cita.fecha_hora_inicio < primer_dia_mes,
        Cita.estado.in_(['completada', 'confirmada'])
    ).scalar() or 0

    # Porcentaje de crecimiento
    crecimiento_ingresos = 0
    if ingresos_mes_anterior > 0:
        crecimiento_ingresos = ((ingresos_mes - ingresos_mes_anterior) / ingresos_mes_anterior) * 100

    # Top 3 Especialistas (por ingresos generados)
    top_especialistas = db.session.query(
        Empleado.nombre, 
        func.sum(Cita.monto_total).label('ingresos_generados'),
        func.count(Cita.id_cita).label('total_citas')
    ).join(Cita, Cita.id_empleado == Empleado.id_empleado)\
     .filter(Cita.estado == 'completada')\
     .group_by(Empleado.id_empleado)\
     .order_by(func.sum(Cita.monto_total).desc())\
     .limit(3).all()

    stats = {
        'citas_hoy': citas_hoy,
        'total_clientes': total_clientes,
        'empleados_activos': empleados_activos,
        'ingresos_mes': float(ingresos_mes),
        'ingresos_mes_anterior': float(ingresos_mes_anterior),
        'crecimiento_ingresos': float(crecimiento_ingresos),
        'top_especialistas': top_especialistas
    }

    return render_template('dashboard_admin.html', stats=stats)


@admin_bp.route('/agenda-diaria')
@admin_required
def agenda_diaria():
    """Agenda del día — vista de todas las citas de hoy"""
    from app.models import Servicio, Empleado
    from sqlalchemy import func

    hoy = datetime.now().date()
    citas_hoy = db.session.query(Cita, Usuario, Empleado, Servicio)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .outerjoin(Empleado, Cita.id_empleado == Empleado.id_empleado)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .filter(func.date(Cita.fecha_hora_inicio) == hoy)\
        .order_by(Cita.fecha_hora_inicio).all()

    return render_template('admin/agenda_diaria.html', citas=citas_hoy, hoy=hoy)

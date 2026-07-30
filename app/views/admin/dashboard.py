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
        Cita.fecha_creacion >= primer_dia_mes,
        Cita.estado.in_(['completada', 'confirmada'])
    ).scalar() or 0

    stats = {
        'citas_hoy': citas_hoy,
        'total_clientes': total_clientes,
        'empleados_activos': empleados_activos,
        'ingresos_mes': ingresos_mes
    }

    return render_template('dashboard_admin.html', stats=stats)

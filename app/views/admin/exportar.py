"""Exportación a Excel de datos de citas y pagos."""
from flask import send_file, flash, redirect, url_for
from app.services.reportes_service import ReportesService
from app.utils.decorators import admin_required
from app.views.admin import admin_bp


@admin_bp.route('/exportar/<tipo>/<periodo>')
@admin_required
def exportar_excel(tipo, periodo):
    """
    Exporta datos de citas, pagos, empleados, servicios, clientes y horarios.
    """
    if tipo not in ['citas', 'pagos', 'empleados', 'servicios', 'clientes', 'horarios']:
        flash('Tipo de exportación no válido.', 'error')
        return redirect(url_for('admin.dashboard'))

    salida = ReportesService.generar_reporte_excel(tipo, periodo)
    return send_file(
        salida,
        as_attachment=True,
        download_name=f"export_{tipo}_{periodo}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

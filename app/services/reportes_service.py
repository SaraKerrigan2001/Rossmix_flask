"""Lógica de generación de reportes para Rossmix."""
import io
import openpyxl
from datetime import datetime, timedelta
from app.models import Cita, Pago, Usuario, Servicio, HorarioEmpleado


class ReportesService:
    @staticmethod
    def _build_periodo_inicio(periodo):
        ahora = datetime.now()
        if periodo == 'diario':
            return ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        if periodo == 'semana':
            return ahora - timedelta(days=7)
        if periodo == 'mes':
            return ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if periodo == 'ano':
            return ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return datetime(1900, 1, 1)

    @staticmethod
    def generar_reporte_excel(tipo, periodo):
        fecha_inicio = ReportesService._build_periodo_inicio(periodo)
        wb = openpyxl.Workbook()
        ws = wb.active

        if tipo == 'citas':
            ws.title = 'Citas'
            ws.append(['ID', 'Código', 'Cliente', 'Servicio', 'Monto', 'Estado', 'Fecha'])
            query = Cita.query.filter(Cita.fecha_creacion >= fecha_inicio).all()
            for c in query:
                cliente = Usuario.query.get(c.id_cliente)
                servicio = Servicio.query.get(c.id_servicio)
                ws.append([
                    c.id_cita,
                    c.codigo_reserva,
                    cliente.nombre if cliente else '',
                    servicio.nombre_servicio if servicio else '',
                    float(c.monto_total or 0),
                    c.estado,
                    c.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                ])

        elif tipo == 'pagos':
            ws.title = 'Pagos'
            ws.append(['ID Pago', 'Código Cita', 'Monto', 'Método', 'Estado', 'Fecha'])
            query = Pago.query.filter(Pago.fecha_pago >= fecha_inicio).all()
            for p in query:
                cita = Cita.query.get(p.id_cita)
                ws.append([
                    p.id_pago,
                    cita.codigo_reserva if cita else '',
                    float(p.monto or 0),
                    p.metodo_pago,
                    p.estado_pago,
                    p.fecha_pago.strftime('%Y-%m-%d %H:%M'),
                ])

        elif tipo == 'clientes':
            ws.title = 'Clientes'
            ws.append(['ID', 'Nombre', 'Email', 'Teléfono', 'Fecha Registro'])
            query = Usuario.query.filter_by(tipo_usuario='cliente').filter(Usuario.fecha_registro >= fecha_inicio).all()
            for c in query:
                ws.append([
                    c.id,
                    c.nombre,
                    c.email,
                    c.telefono,
                    c.fecha_registro.strftime('%Y-%m-%d %H:%M'),
                ])

        elif tipo == 'servicios':
            ws.title = 'Servicios'
            ws.append(['ID', 'Nombre', 'Descripción', 'Precio', 'Duración'])
            query = Servicio.query.all()
            for s in query:
                ws.append([
                    s.id_servicio,
                    s.nombre_servicio,
                    s.descripcion,
                    float(s.precio_total or 0),
                    s.duracion_minutos,
                ])

        elif tipo == 'horarios':
            ws.title = 'Horarios'
            ws.append(['ID Horario', 'Empleado', 'Día', 'Hora Inicio', 'Hora Fin'])
            query = HorarioEmpleado.query.all()
            for h in query:
                empleado = Usuario.query.get(h.id_empleado)
                ws.append([
                    h.id_horario,
                    empleado.nombre if empleado else '',
                    h.dia_semana,
                    h.hora_inicio.strftime('%H:%M'),
                    h.hora_fin.strftime('%H:%M'),
                ])

        else:
            ws.title = 'Datos'
            ws.append(['No hay datos para el tipo solicitado.'])

        salida = io.BytesIO()
        wb.save(salida)
        salida.seek(0)
        return salida

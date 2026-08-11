"""Lógica de generación de reportes para Rossmix."""
import io
import openpyxl
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import Cita, Pago, Usuario, Servicio, HorarioEmpleado, Empleado


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
            # JOIN en una sola query — evita N+1
            query = (
                db.session.query(Cita, Usuario, Servicio)
                .join(Usuario, Cita.id_cliente == Usuario.id)
                .join(Servicio, Cita.id_servicio == Servicio.id_servicio)
                .filter(Cita.fecha_creacion >= fecha_inicio)
                .order_by(Cita.fecha_creacion.desc())
                .all()
            )
            for c, cliente, servicio in query:
                ws.append([
                    c.id_cita,
                    c.codigo_reserva,
                    cliente.nombre,
                    servicio.nombre_servicio,
                    float(c.monto_total or 0),
                    c.estado,
                    c.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                ])

        elif tipo == 'pagos':
            ws.title = 'Pagos'
            ws.append(['ID Pago', 'Código Cita', 'Monto', 'Método', 'Estado', 'Fecha'])
            # JOIN en una sola query — evita N+1
            query = (
                db.session.query(Pago, Cita)
                .join(Cita, Pago.id_cita == Cita.id_cita)
                .filter(Pago.fecha_pago >= fecha_inicio)
                .order_by(Pago.fecha_pago.desc())
                .all()
            )
            for p, cita in query:
                ws.append([
                    p.id_pago,
                    cita.codigo_reserva,
                    float(p.monto or 0),
                    p.metodo_pago,
                    p.estado_pago,
                    p.fecha_pago.strftime('%Y-%m-%d %H:%M'),
                ])

        elif tipo == 'clientes':
            ws.title = 'Clientes'
            ws.append(['ID', 'Nombre', 'Email', 'Teléfono', 'Fecha Registro'])
            query = (
                Usuario.query
                .filter_by(tipo_usuario='cliente')
                .filter(Usuario.fecha_registro >= fecha_inicio)
                .order_by(Usuario.nombre)
                .all()
            )
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
            ws.append(['ID', 'Nombre', 'Descripción', 'Precio', 'Duración (min)', 'Activo'])
            query = Servicio.query.order_by(Servicio.nombre_servicio).all()
            for s in query:
                ws.append([
                    s.id_servicio,
                    s.nombre_servicio,
                    s.descripcion or '',
                    float(s.precio_total or 0),
                    s.duracion_minutos,
                    'Sí' if s.activo else 'No',
                ])

        elif tipo == 'empleados':
            ws.title = 'Empleados'
            ws.append(['ID', 'Nombre', 'Especialidad', 'Activo', 'Fecha Registro'])
            query = Empleado.query.order_by(Empleado.nombre).all()
            for e in query:
                ws.append([
                    e.id_empleado,
                    e.nombre,
                    e.especialidad or '',
                    'Sí' if e.activo else 'No',
                    e.fecha_registro.strftime('%Y-%m-%d') if e.fecha_registro else '',
                ])

        elif tipo == 'horarios':
            ws.title = 'Horarios'
            ws.append(['ID Horario', 'Empleado', 'Día', 'Hora Inicio', 'Hora Fin'])
            # FIX: usar Empleado (no Usuario) — JOIN en una sola query para evitar N+1
            query = (
                db.session.query(HorarioEmpleado, Empleado)
                .join(Empleado, HorarioEmpleado.id_empleado == Empleado.id_empleado)
                .order_by(Empleado.nombre, HorarioEmpleado.dia_semana)
                .all()
            )
            dias = {0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
                    4: 'Jueves', 5: 'Viernes', 6: 'Sábado'}
            for h, empleado in query:
                ws.append([
                    h.id_horario,
                    empleado.nombre,
                    dias.get(h.dia_semana, str(h.dia_semana)),
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

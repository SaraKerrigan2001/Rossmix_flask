"""Modelo de Empleado."""
from datetime import datetime, timedelta
from app.extensions import db


class Empleado(db.Model):
    """Empleados del salón"""
    __tablename__ = 'empleados'

    # ── Paso 2: Variables (columnas) ──────────────────────────────────────
    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    # ── Relaciones ────────────────────────────────────────────────────────
    horarios = db.relationship('HorarioEmpleado', backref='empleado', lazy=True, cascade='all, delete-orphan')
    citas = db.relationship('Cita', backref='empleado', lazy=True)

    # ── Paso 3: Constructor ───────────────────────────────────────────────
    def __init__(self, nombre=None, especialidad=None, activo=True, id_usuario=None):
        self.nombre = nombre
        self.especialidad = especialidad
        self.activo = activo
        self.id_usuario = id_usuario

    # ── Paso 5: Encapsulamiento (propiedades) ─────────────────────────────

    @property
    def citas_hoy(self):
        """Citas asignadas a este empleado para el día de hoy."""
        from app.models.cita import Cita
        from app.models.usuario import Usuario
        from app.models.servicio import Servicio

        hoy = datetime.now().date()
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        fin_dia = datetime.combine(hoy, datetime.max.time())

        return db.session.query(Cita, Usuario, Servicio)\
            .join(Usuario, Cita.id_cliente == Usuario.id)\
            .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
            .filter(
                Cita.id_empleado == self.id_empleado,
                Cita.fecha_hora_inicio >= inicio_dia,
                Cita.fecha_hora_inicio <= fin_dia,
                Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion', 'completada'])
            ).order_by(Cita.fecha_hora_inicio).all()

    @property
    def citas_proximas(self):
        """Próximas 10 citas activas asignadas a este empleado."""
        from app.models.cita import Cita
        from app.models.usuario import Usuario
        from app.models.servicio import Servicio

        return db.session.query(Cita, Usuario, Servicio)\
            .join(Usuario, Cita.id_cliente == Usuario.id)\
            .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
            .filter(
                Cita.id_empleado == self.id_empleado,
                Cita.fecha_hora_inicio >= datetime.now(),
                Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion'])
            ).order_by(Cita.fecha_hora_inicio).limit(10).all()

    @property
    def completadas_mes(self):
        """Total de citas completadas este mes."""
        from app.models.cita import Cita
        from sqlalchemy import extract

        hoy = datetime.now()
        return Cita.query.filter(
            Cita.id_empleado == self.id_empleado,
            Cita.estado == 'completada',
            extract('month', Cita.fecha_hora_inicio) == hoy.month,
            extract('year', Cita.fecha_hora_inicio) == hoy.year
        ).count()

    @property
    def ingresos_mes(self):
        """Suma de monto_total de citas completadas este mes."""
        from app.models.cita import Cita
        from sqlalchemy import func, extract

        hoy = datetime.now()
        resultado = db.session.query(
            func.coalesce(func.sum(Cita.monto_total), 0)
        ).filter(
            Cita.id_empleado == self.id_empleado,
            Cita.estado == 'completada',
            extract('month', Cita.fecha_hora_inicio) == hoy.month,
            extract('year', Cita.fecha_hora_inicio) == hoy.year
        ).scalar()
        return float(resultado) if resultado else 0.0

    # ── Paso 6: Métodos de negocio ────────────────────────────────────────

    def obtener_servicios(self):
        """Retorna los IDs de los servicios que este empleado puede realizar."""
        from app.models.servicio import EmpleadoServicio
        relaciones = EmpleadoServicio.query.filter_by(
            id_empleado=self.id_empleado
        ).all()
        return [r.id_servicio for r in relaciones]

    def obtener_citas_disponibles(self):
        """Citas sin asignar que coinciden con los servicios de este empleado."""
        from app.models.cita import Cita
        from app.models.usuario import Usuario
        from app.models.servicio import Servicio

        mis_servicios = self.obtener_servicios()
        if not mis_servicios:
            return []

        return db.session.query(Cita, Usuario, Servicio)\
            .join(Usuario, Cita.id_cliente == Usuario.id)\
            .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
            .filter(
                Cita.id_empleado.is_(None),
                Cita.id_servicio.in_(mis_servicios),
                Cita.estado.in_(['pendiente_pago', 'confirmada']),
                Cita.fecha_hora_inicio >= datetime.now()
            ).order_by(Cita.fecha_hora_inicio).all()

    def cambiar_estado_cita(self, id_cita, nuevo_estado):
        """
        Cambia el estado de una cita asignada a este empleado.

        Transiciones permitidas:
            confirmada     → en_atencion
            en_atencion    → completada

        Returns:
            dict con 'success' (bool) y 'message' (str)
        """
        from app.models.cita import Cita

        TRANSICIONES = {
            'confirmada': ['en_atencion'],
            'en_atencion': ['completada'],
        }

        try:
            cita = db.session.get(Cita, id_cita)
            if not cita:
                return {'success': False, 'message': 'Cita no encontrada'}

            if cita.id_empleado != self.id_empleado:
                return {'success': False, 'message': 'Esta cita no está asignada a ti'}

            estado_actual = cita.estado
            permitidos = TRANSICIONES.get(estado_actual, [])

            if nuevo_estado not in permitidos:
                return {
                    'success': False,
                    'message': f'No se puede cambiar de "{estado_actual}" a "{nuevo_estado}"'
                }

            cita.estado = nuevo_estado
            db.session.commit()

            return {
                'success': True,
                'message': f'Cita actualizada a "{nuevo_estado.replace("_", " ").title()}"',
                'nuevo_estado': nuevo_estado
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error al actualizar: {str(e)}'}

    def __repr__(self):
        return f'<Empleado {self.nombre}>'

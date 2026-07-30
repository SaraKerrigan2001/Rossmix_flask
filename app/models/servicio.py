"""Modelo de Servicio y tabla intermedia EmpleadoServicio."""
from app.extensions import db


class Servicio(db.Model):
    """Servicios ofrecidos por el salón"""
    __tablename__ = 'servicios'

    id_servicio = db.Column(db.Integer, primary_key=True)
    nombre_servicio = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)
    duracion_minutos = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    citas = db.relationship('Cita', backref='servicio', lazy=True)
    empleados = db.relationship('Empleado', secondary='empleado_servicios', backref='servicios')

    def __repr__(self):
        return f'<Servicio {self.nombre_servicio}>'


class EmpleadoServicio(db.Model):
    """Relación empleados-servicios (Tabla intermedia Many-to-Many)"""
    __tablename__ = 'empleado_servicios'

    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='CASCADE'), primary_key=True)
    id_servicio = db.Column(db.Integer, db.ForeignKey('servicios.id_servicio', ondelete='CASCADE'), primary_key=True)

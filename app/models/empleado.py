"""Modelo de Empleado."""
from datetime import datetime
from app.extensions import db


class Empleado(db.Model):
    """Empleados del salón"""
    __tablename__ = 'empleados'

    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    horarios = db.relationship('HorarioEmpleado', backref='empleado', lazy=True, cascade='all, delete-orphan')
    citas = db.relationship('Cita', backref='empleado', lazy=True)

    def __repr__(self):
        return f'<Empleado {self.nombre}>'

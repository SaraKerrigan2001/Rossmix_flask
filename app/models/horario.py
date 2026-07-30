"""Modelo de HorarioEmpleado."""
from app.extensions import db


class HorarioEmpleado(db.Model):
    """Horarios de trabajo de los empleados"""
    __tablename__ = 'horarios_empleados'

    id_horario = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='CASCADE'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Domingo, 1=Lunes, ..., 6=Sábado
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<HorarioEmpleado {self.empleado.nombre if self.empleado else "N/A"} - Día {self.dia_semana}>'

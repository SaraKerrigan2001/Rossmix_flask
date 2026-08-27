"""Modelo de Cita."""
from datetime import datetime
from app.extensions import db


class Cita(db.Model):
    """Citas agendadas"""
    __tablename__ = 'citas'

    id_cita = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='SET NULL'))
    id_servicio = db.Column(db.Integer, db.ForeignKey('servicios.id_servicio', ondelete='RESTRICT'), nullable=False)
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False)
    fecha_hora_fin = db.Column(db.DateTime, nullable=False)
    monto_total = db.Column(db.Numeric(10, 2))
    monto_abono = db.Column(db.Numeric(10, 2), default=5000)
    saldo_pendiente = db.Column(db.Numeric(10, 2))
    estado            = db.Column(
        db.Enum(
            'pendiente_pago', 'confirmada', 'en_atencion',
            'completada', 'cancelada', 'no_asistio',
            name='estado_cita_enum', create_type=False,
        ),
        nullable=False, default='pendiente_pago', index=True,
    )
    reembolsado = db.Column(db.Boolean, default=False)
    codigo_reserva = db.Column(db.String(20), unique=True)
    token_gestion = db.Column(db.String(32), unique=True)  # Token URL-safe para link de gestión/reprogramación
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    # Relación con pagos (una cita tiene máximo un pago)
    pago = db.relationship('Pago', backref='cita', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Cita {self.id_cita} - {self.estado}>'

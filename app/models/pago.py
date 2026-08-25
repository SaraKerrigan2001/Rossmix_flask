"""Modelo de Pago."""
from datetime import datetime
from app.extensions import db


class Pago(db.Model):
    """Pagos registrados por cada cita"""
    __tablename__ = 'pagos'

    id_pago = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id_cita', ondelete='CASCADE'),
                        nullable=False, unique=True)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(
        db.Enum(
            'efectivo',
            'tarjeta',
            'transferencia',
            'nequi',
            'daviplata',
            name='metodo_pago_enum',
            create_type=False,   # el tipo ya existe en PostgreSQL (creado por Rossmix.sql)
        ),
        nullable=False,
        default='efectivo',
    )
    estado_pago = db.Column(db.String(20), nullable=False, default='completado')
    referencia = db.Column(db.String(100))
    fecha_pago = db.Column(db.DateTime, default=datetime.now)
    notas = db.Column(db.Text)

    def __repr__(self):
        return f'<Pago {self.id_pago} - Cita {self.id_cita} - ${self.monto}>'

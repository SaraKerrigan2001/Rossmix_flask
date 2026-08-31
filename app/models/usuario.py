"""Modelo de Usuario (clientes, administradores y especialistas)."""
import re
from datetime import datetime

from sqlalchemy.orm import validates

from app.extensions import db


class Usuario(db.Model):
    """Usuarios del sistema: cliente | admin | especialista"""
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.synonym('id')
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tipo_usuario   = db.Column(db.String(20), nullable=False, index=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    activo         = db.Column(db.Boolean, default=True)

    # Vínculo opcional con empleado (solo para tipo_usuario='especialista')
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='SET NULL'), nullable=True)
    empleado_vinculado = db.relationship('Empleado', foreign_keys=[id_empleado], backref='usuario_cuenta', uselist=False)

    # Foto de perfil (ruta relativa a static/uploads/perfiles/)
    foto_perfil = db.Column(db.String(200), nullable=True)

    # Relaciones
    citas = db.relationship('Cita', backref='cliente', lazy=True, foreign_keys='Cita.id_cliente')
    notificaciones = db.relationship('Notificacion', backref='usuario', lazy=True)

    def __init__(self, nombre=None, email=None, telefono=None, password=None,
                 tipo_usuario=None, activo=True, fecha_registro=None, id_empleado=None):
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.password = password
        self.tipo_usuario = tipo_usuario
        self.activo = activo
        self.id_empleado = id_empleado
        if fecha_registro:
            self.fecha_registro = fecha_registro

    @validates('telefono')
    def validate_telefono(self, key, value):
        """Garantiza que el teléfono tenga exactamente 10 dígitos."""
        if value is None:
            raise ValueError('El teléfono es obligatorio.')

        telefono = str(value).strip()
        if not re.fullmatch(r'\d{10}', telefono):
            raise ValueError('El teléfono debe contener exactamente 10 dígitos numéricos.')
        return telefono

    @property
    def es_especialista(self):
        return self.tipo_usuario == 'especialista'

    @property
    def citas_completadas(self):
        """Cuenta citas completadas directamente en BD — evita cargar todas en memoria."""
        from app.models.cita import Cita as CitaModel
        return db.session.query(db.func.count(CitaModel.id_cita)).filter(
            CitaModel.id_cliente == self.id,
            CitaModel.estado == 'completada'
        ).scalar() or 0

    @property
    def nivel_fidelidad(self):
        citas = self.citas_completadas
        if citas < 3:
            return 'Bronce'
        elif citas < 6:
            return 'Plata'
        else:
            return 'Oro'
            
    @property
    def faltantes_siguiente_nivel(self):
        citas = self.citas_completadas
        if citas < 3:
            return 3 - citas
        elif citas < 6:
            return 6 - citas
        else:
            return 0 # Nivel máximo alcanzado

    def __repr__(self):
        return f'<Usuario {self.nombre} - {self.tipo_usuario}>'

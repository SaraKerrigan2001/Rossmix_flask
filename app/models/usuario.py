"""Modelo de Usuario (clientes, administradores y especialistas)."""
from datetime import datetime
from app.extensions import db


class Usuario(db.Model):
    """Usuarios del sistema: cliente | admin | especialista"""
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)  # 'cliente' | 'admin' | 'especialista'
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

    # Vínculo opcional con empleado (solo para tipo_usuario='especialista')
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='SET NULL'), nullable=True)
    empleado_vinculado = db.relationship('Empleado', foreign_keys=[id_empleado], backref='usuario_cuenta', uselist=False)

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

    @property
    def es_especialista(self):
        return self.tipo_usuario == 'especialista'

    @property
    def citas_completadas(self):
        return sum(1 for c in self.citas if c.estado == 'completada')

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

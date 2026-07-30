"""Modelo de Usuario (clientes y administradores)."""
from datetime import datetime
from app.extensions import db


class Usuario(db.Model):
    """Usuarios del sistema (clientes y administradores)"""
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    citas = db.relationship('Cita', backref='cliente', lazy=True, foreign_keys='Cita.id_cliente')
    # Notificaciones del usuario
    notificaciones = db.relationship('Notificacion', backref='usuario', lazy=True)

    def __init__(self, nombre=None, email=None, telefono=None, password=None, tipo_usuario=None, activo=True, fecha_registro=None):
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.password = password
        self.tipo_usuario = tipo_usuario
        self.activo = activo
        if fecha_registro:
            self.fecha_registro = fecha_registro

    def __repr__(self):
        return f'<Usuario {self.nombre} - {self.tipo_usuario}>'

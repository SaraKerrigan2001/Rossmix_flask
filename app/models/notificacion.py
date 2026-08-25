"""Modelo de Notificación."""
from datetime import datetime
from app.extensions import db


class Notificacion(db.Model):
    """Notificaciones para usuarios"""
    __tablename__ = 'notificaciones'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text)
    target = db.Column(db.String(300))
    leido = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Notificacion {self.id} -> Usuario {self.id_usuario} - {self.titulo}>'

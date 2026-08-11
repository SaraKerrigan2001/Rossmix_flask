"""Modelo de Auditoría de Usuarios."""
from datetime import datetime
from app.extensions import db


class AuditoriaUsuario(db.Model):
    """
    Registro de auditoría de acciones sobre cuentas de usuario.

    Relaciones:
        usuario_afectado → Usuario  (id_usuario, SET NULL al borrar)
        usuario_actor    → Usuario  (id_actor,   SET NULL al borrar)
    """
    __tablename__ = 'auditoria_usuarios'

    id           = db.Column(db.Integer, primary_key=True)

    # Usuario que fue afectado por la acción
    id_usuario   = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id', ondelete='SET NULL'),
        nullable=True,
    )

    # Usuario que realizó la acción (ej: admin que editó la cuenta)
    id_actor     = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id', ondelete='SET NULL'),
        nullable=True,
    )

    # Snapshot de los datos del usuario al momento de la acción
    nombre       = db.Column(db.String(100))
    email        = db.Column(db.String(120))
    telefono     = db.Column(db.String(20))
    tipo_usuario = db.Column(db.String(20))

    # Datos de la acción
    accion       = db.Column(db.String(50), nullable=False)  # crear|editar|desactivar|login|logout|reset_password
    detalle      = db.Column(db.Text)
    ip_address   = db.Column(db.String(45))
    fecha        = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuario_afectado = db.relationship(
        'Usuario',
        foreign_keys=[id_usuario],
        backref=db.backref('auditoria_recibida', lazy=True),
    )
    usuario_actor = db.relationship(
        'Usuario',
        foreign_keys=[id_actor],
        backref=db.backref('auditoria_realizada', lazy=True),
    )

    def __repr__(self):
        return f'<Auditoria {self.accion} usuario={self.id_usuario} actor={self.id_actor}>'


def registrar_auditoria(accion, id_usuario=None, id_actor=None,
                        nombre=None, email=None, telefono=None,
                        tipo_usuario=None, detalle=None, ip_address=None):
    """
    Función helper para registrar una entrada de auditoría.

    Uso:
        from app.models.auditoria import registrar_auditoria
        registrar_auditoria(
            accion='editar',
            id_usuario=cliente.id,
            id_actor=session.get('usuario_id'),
            nombre=cliente.nombre,
            email=cliente.email,
            detalle='Cambió teléfono de 300 a 310',
            ip_address=request.remote_addr,
        )
    """
    from app.extensions import db
    entrada = AuditoriaUsuario(
        accion=accion,
        id_usuario=id_usuario,
        id_actor=id_actor,
        nombre=nombre,
        email=email,
        telefono=telefono,
        tipo_usuario=tipo_usuario,
        detalle=detalle,
        ip_address=ip_address,
    )
    db.session.add(entrada)
    # No hacemos commit aquí — se hace junto con la transacción principal

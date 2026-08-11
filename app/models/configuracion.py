"""Modelo de configuración del sistema."""
from datetime import datetime
from app.extensions import db


class Configuracion(db.Model):
    """
    Parámetros configurables del sistema (clave-valor).

    Relaciones:
        usuario_creador    → Usuario  (creado_por,    SET NULL al borrar)
        usuario_modificador → Usuario (modificado_por, SET NULL al borrar)
    """
    __tablename__ = 'configuraciones'

    id          = db.Column(db.Integer, primary_key=True)
    clave       = db.Column(db.String(120), unique=True, nullable=False)
    valor       = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)

    # FK → usuario que creó el parámetro
    creado_por = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id', ondelete='SET NULL'),
        nullable=True,
    )

    # FK → usuario que lo modificó por última vez
    modificado_por = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id', ondelete='SET NULL'),
        nullable=True,
    )

    fecha_creacion       = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion  = db.Column(db.DateTime, default=datetime.utcnow,
                                     onupdate=datetime.utcnow)

    # Relaciones
    usuario_creador = db.relationship(
        'Usuario',
        foreign_keys=[creado_por],
        backref=db.backref('configuraciones_creadas', lazy=True),
    )
    usuario_modificador = db.relationship(
        'Usuario',
        foreign_keys=[modificado_por],
        backref=db.backref('configuraciones_modificadas', lazy=True),
    )

    def __repr__(self):
        return f'<Configuracion {self.clave}={self.valor}>'

    @staticmethod
    def obtener(clave, default=None):
        """Obtiene el valor de una clave de configuración."""
        config = Configuracion.query.filter_by(clave=clave).first()
        return config.valor if config else default

    @staticmethod
    def establecer(clave, valor, id_usuario=None, descripcion=None):
        """Crea o actualiza una clave de configuración."""
        config = Configuracion.query.filter_by(clave=clave).first()
        if config:
            config.valor          = valor
            config.modificado_por = id_usuario
            config.fecha_actualizacion = datetime.utcnow()
        else:
            config = Configuracion(
                clave=clave,
                valor=valor,
                descripcion=descripcion,
                creado_por=id_usuario,
                modificado_por=id_usuario,
            )
            from app.extensions import db as _db
            _db.session.add(config)
        return config

"""
Application Factory de Rossmix Flask.
"""
import os
from flask import Flask
from werkzeug.security import generate_password_hash
from app.config import Config
from app.extensions import db
from app.utils.helpers import inject_notificaciones


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)

    # Registrar context processor
    app.context_processor(inject_notificaciones)

    # Mapeo de compatibilidad de endpoints para url_for
    from flask import url_for as flask_url_for
    URL_MAPPING = {
        'index': 'main.index',
        'test_image': 'main.test_image',
        'login': 'auth.login',
        'registro': 'auth.registro',
        'logout': 'auth.logout',
        'dashboard_cliente': 'cliente.dashboard_cliente',
        'dashboard_admin': 'admin.dashboard',
        'notificaciones': 'notif.notificaciones',
        'notificacion_marcar_leida': 'notif.marcar_leida',
        'notificaciones_marcar_todas': 'notif.marcar_todas',
        'agendar_paso1': 'citas.agendar_paso1',
        'agendar_paso2': 'citas.agendar_paso2',
        'agendar_paso3': 'citas.agendar_paso3',
        'horarios_disponibles': 'citas.horarios_disponibles',
        'agendar_paso4': 'citas.agendar_paso4',
        'confirmar_cita': 'citas.confirmar_cita',
        'cita_confirmada': 'citas.cita_confirmada',
        'mis_citas': 'citas.mis_citas',
        'cancelar_cita': 'citas.cancelar_cita',
        'cliente_pagos_registrar': 'citas.cliente_pagos_registrar',
        'admin_exportar_excel': 'admin.exportar_excel',
        'admin_empleados': 'admin.empleados',
        'admin_empleados_crear': 'admin.empleados_crear',
        'admin_empleados_editar': 'admin.empleados_editar',
        'admin_empleados_eliminar': 'admin.empleados_eliminar',
        'admin_servicios': 'admin.servicios',
        'admin_servicios_crear': 'admin.servicios_crear',
        'admin_servicios_editar': 'admin.servicios_editar',
        'admin_servicios_eliminar': 'admin.servicios_eliminar',
        'admin_clientes': 'admin.clientes',
        'admin_clientes_hoy': 'admin.clientes_hoy',
        'admin_clientes_editar': 'admin.clientes_editar',
        'admin_clientes_eliminar': 'admin.clientes_eliminar',
        'admin_horarios': 'admin.horarios',
        'admin_horarios_crear': 'admin.horarios_crear',
        'admin_horarios_editar': 'admin.horarios_editar',
        'admin_horarios_eliminar': 'admin.horarios_eliminar',
        'admin_citas': 'admin.citas',
        'admin_citas_cambiar_estado': 'admin.citas_cambiar_estado',
        'admin_pagos': 'admin.pagos',
        'admin_pagos_registrar': 'admin.pagos_registrar',
        'admin_pagos_eliminar': 'admin.pagos_eliminar'
    }

    def smart_url_for(endpoint, **values):
        mapped_endpoint = URL_MAPPING.get(endpoint, endpoint)
        return flask_url_for(mapped_endpoint, **values)

    app.jinja_env.globals['url_for'] = smart_url_for

    # Registrar blueprints
    from app.views import main_bp, auth_bp, cliente_bp, citas_bp, notif_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(citas_bp)
    app.register_blueprint(notif_bp)
    app.register_blueprint(admin_bp)

    # Crear tablas y usuario administrador por defecto si no existen
    with app.app_context():
        db.create_all()

        # Importación tardía para evitar ciclos
        from app.models.usuario import Usuario

        admin_email    = os.environ.get('ADMIN_EMAIL',    'admin@rossmix.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')

        admin = Usuario.query.filter_by(email=admin_email).first()
        if not admin:
            if not admin_password:
                # No se creó ADMIN_PASSWORD: no generamos un admin con
                # contraseña predecible. Definir ADMIN_PASSWORD en el .env
                # para que el administrador por defecto se cree.
                print(
                    'Aviso: no se creó el usuario administrador por defecto '
                    'porque falta la variable de entorno ADMIN_PASSWORD.'
                )
            else:
                admin = Usuario(
                    nombre='Administrador',
                    email=admin_email,
                    telefono='3000000000',
                    password=generate_password_hash(admin_password),
                    tipo_usuario='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print(f'Usuario administrador creado por defecto: {admin_email}')

    return app

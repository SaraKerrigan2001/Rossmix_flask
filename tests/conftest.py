"""
Pytest configuration and shared fixtures para Rossmix.
Este archivo define fixtures globales que se reutilizan en todos los tests.
"""
import os

os.environ.setdefault("APP_TESTING", "1")
os.environ.setdefault("FLASK_ENV", "testing")

import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.config import Config
from app.extensions import db
from app.models.usuario import Usuario


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture(scope="session")
def app():
    """Crea una instancia de aplicación Flask para testing."""
    app = create_app(config_class=TestConfig)
    return app


@pytest.fixture(scope="session")
def app_context(app):
    """Establece el contexto de aplicación para la sesión de tests."""
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def client(app, app_context):
    """Crea un cliente de prueba Flask."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def db_session(app, app_context):
    """Crea una sesión de base de datos limpia para cada test."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def admin_user(db_session, app_context):
    """Crea un usuario administrador para testing."""
    admin = Usuario(
        nombre="Admin Test",
        email="admin@test.com",
        telefono="3000000000",
        password=generate_password_hash("admin123"),
        tipo_usuario="admin",
        activo=True,
    )
    db_session.session.add(admin)
    db_session.session.commit()
    return admin


@pytest.fixture(scope="function")
def cliente_user(db_session, app_context):
    """Crea un usuario cliente para testing."""
    cliente = Usuario(
        nombre="Cliente Test",
        email="cliente@test.com",
        telefono="3111111111",
        password=generate_password_hash("cliente123"),
        tipo_usuario="cliente",
        activo=True,
    )
    db_session.session.add(cliente)
    db_session.session.commit()
    return cliente


@pytest.fixture(scope="function")
def especialista_user(db_session, app_context):
    """Crea un usuario especialista para testing."""
    from app.models.empleado import Empleado

    especialista = Usuario(
        nombre="Especialista Test",
        email="especialista@test.com",
        telefono="3222222222",
        password=generate_password_hash("especialista123"),
        tipo_usuario="especialista",
        activo=True,
    )
    db_session.session.add(especialista)
    db_session.session.flush()

    empleado = Empleado(
        nombre="Especialista Test",
        especialidad="Manicure",
        activo=True,
        id_usuario=especialista.id_usuario,
    )
    db_session.session.add(empleado)
    especialista.id_empleado = empleado.id_empleado
    db_session.session.commit()
    return especialista


@pytest.fixture(scope="function")
def admin_logged_in(client, admin_user):
    """Cliente con sesión de admin iniciada."""
    with client.session_transaction() as sess:
        sess["usuario_id"] = admin_user.id_usuario
        sess["tipo_usuario"] = "admin"
    return client


@pytest.fixture(scope="function")
def cliente_logged_in(client, cliente_user):
    """Cliente con sesión de cliente iniciada."""
    with client.session_transaction() as sess:
        sess["usuario_id"] = cliente_user.id_usuario
        sess["tipo_usuario"] = "cliente"
    return client


@pytest.fixture(scope="function")
def especialista_logged_in(client, especialista_user):
    """Cliente con sesión de especialista iniciada."""
    with client.session_transaction() as sess:
        sess["usuario_id"] = especialista_user.id_usuario
        sess["tipo_usuario"] = "especialista"
    return client

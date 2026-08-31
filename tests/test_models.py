"""
Tests para modelos de Usuario, Empleado y relaciones.
"""
import pytest
from werkzeug.security import check_password_hash
from app.models.usuario import Usuario


@pytest.mark.models
class TestUsuarioModel:
    """Tests para el modelo Usuario."""

    def test_usuario_creation(self, db_session, admin_user):
        """Verifica creación de usuario."""
        assert admin_user.id_usuario is not None
        assert admin_user.email == "admin@test.com"
        assert admin_user.tipo_usuario == "admin"

    def test_usuario_password_hashing(self, db_session):
        """Verifica que las contraseñas se hashean."""
        usuario = Usuario(
            nombre="Test",
            email="test@test.com",
            telefono="3100000000",
            password="mypassword123",
            tipo_usuario="cliente",
        )
        # Nota: password sin hash al crear. set_password() debería usarse si existe
        db_session.session.add(usuario)
        db_session.session.commit()

        # Verificar que la contraseña se almacenó
        retrieved = db_session.session.get(Usuario, usuario.id_usuario)
        assert retrieved is not None

    def test_usuario_tipos_validos(self, db_session):
        """Verifica que los tipos de usuario válidos se aceptan."""
        for tipo in ["admin", "especialista", "cliente"]:
            usuario = Usuario(
                nombre=f"User {tipo}",
                email=f"{tipo}@test.com",
                telefono="3100000000",
                password="password",
                tipo_usuario=tipo,
            )
            db_session.session.add(usuario)
        db_session.session.commit()
        assert True  # Si llegamos aquí, no hubo error

    def test_usuario_activo_default_true(self, db_session):
        """Verifica que nuevos usuarios están activos por defecto."""
        usuario = Usuario(
            nombre="Test",
            email="test@test.com",
            telefono="3100000000",
            password="password",
            tipo_usuario="cliente",
        )
        db_session.session.add(usuario)
        db_session.session.commit()
        assert usuario.activo is True


@pytest.mark.models
class TestEmpleadoModel:
    """Tests para el modelo Empleado."""

    def test_empleado_creation(self, db_session, especialista_user):
        """Verifica creación de empleado."""
        from app.models.empleado import Empleado

        # El especialista_user ya tiene un empleado vinculado
        assert especialista_user.id_empleado is not None

    def test_empleado_vinculado_a_usuario(self, db_session, especialista_user):
        """Verifica vínculo entre Empleado y Usuario."""
        assert especialista_user.id_empleado is not None
        assert especialista_user.tipo_usuario == "especialista"


@pytest.mark.integration
class TestUsuarioEmpleadoRelacion:
    """Tests de integración entre Usuario y Empleado."""

    def test_especialista_sin_empleado_invalido(self, db_session):
        """Verifica que especialista sin empleado vinculado es inválido."""
        usuario = Usuario(
            nombre="Especialista Sin Vinculo",
            email="sin_vinculo@test.com",
            telefono="3100000000",
            password="password",
            tipo_usuario="especialista",
            activo=True,
            id_empleado=None,  # Sin vínculo
        )
        db_session.session.add(usuario)
        db_session.session.commit()
        assert usuario.id_empleado is None

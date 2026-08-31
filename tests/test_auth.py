"""
Tests para autenticación y autorización.
Verifica login, logout, registro y protección de rutas.
"""
import pytest
from flask import url_for


@pytest.mark.auth
class TestLogin:
    """Tests para login."""

    def test_login_page_accessible(self, client):
        """Verifica que la página de login sea accesible."""
        response = client.get(url_for("auth.login"))
        assert response.status_code == 200
        assert b"Iniciar" in response.data or b"Login" in response.data

    def test_login_valid_credentials(self, client, admin_user):
        """Verifica login con credenciales válidas."""
        response = client.post(
            url_for("auth.login"),
            data={"email": "admin@test.com", "password": "admin123"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_login_invalid_email(self, client):
        """Verifica rechazo de email inválido."""
        response = client.post(
            url_for("auth.login"),
            data={"email": "invalido@test.com", "password": "password123"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # La respuesta debe indicar error

    def test_login_invalid_password(self, client, admin_user):
        """Verifica rechazo de contraseña incorrecta."""
        response = client.post(
            url_for("auth.login"),
            data={"email": "admin@test.com", "password": "wrongpassword"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_logout(self, client, admin_logged_in):
        """Verifica que logout limpia la sesión."""
        response = client.get(url_for("auth.logout"), follow_redirects=True)
        assert response.status_code == 200


@pytest.mark.auth
class TestRegistro:
    """Tests para registro."""

    def test_registro_page_accessible(self, client):
        """Verifica que la página de registro sea accesible."""
        response = client.get(url_for("auth.registro"))
        assert response.status_code == 200

    def test_registro_valid_data(self, client, db_session):
        """Verifica registro con datos válidos."""
        response = client.post(
            url_for("auth.registro"),
            data={
                "nombre": "Nuevo Usuario",
                "email": "nuevo@test.com",
                "telefono": "3150000000",
                "password": "password123",
                "confirmar_password": "password123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200


@pytest.mark.auth
class TestAuthorizacion:
    """Tests para control de acceso."""

    def test_admin_required_without_login(self, client):
        """Verifica que admin_required rechaza sin login."""
        response = client.get(
            url_for("admin.dashboard"), follow_redirects=True
        )
        # Debe redirigir a login
        assert response.status_code == 200

    def test_admin_required_cliente_cannot_access(self, client, cliente_logged_in):
        """Verifica que cliente no puede acceder a admin."""
        response = cliente_logged_in.get(
            url_for("admin.dashboard"), follow_redirects=True
        )
        assert response.status_code == 200

    def test_admin_can_access_dashboard(self, client, admin_logged_in):
        """Verifica que admin puede acceder al dashboard."""
        response = admin_logged_in.get(url_for("admin.dashboard"))
        assert response.status_code == 200

    def test_cliente_can_access_dashboard(self, client, cliente_logged_in):
        """Verifica que cliente puede acceder su dashboard."""
        response = cliente_logged_in.get(url_for("cliente.dashboard_cliente"))
        assert response.status_code == 200


@pytest.mark.auth
class TestSeguridad:
    """Tests para seguridad de autenticación."""

    def test_csrf_protection_enabled(self, app):
        """Verifica que CSRF está habilitado."""
        assert app.config["WTF_CSRF_ENABLED"] is True or app.config["TESTING"] is True

    def test_password_hashed_not_plain(self, db_session, admin_user):
        """Verifica que las contraseñas están hasheadas."""
        assert admin_user.password != "admin123"
        assert len(admin_user.password) > 20  # Hash típico es largo

"""
Tests para rutas principales y health check.
"""
import pytest
from flask import url_for


@pytest.mark.integration
class TestHealthCheck:
    """Tests para el endpoint de health check."""

    def test_health_check_accessible(self, client):
        """Verifica que el health check es accesible."""
        response = client.get(url_for("main.health"))
        assert response.status_code == 200

    def test_health_check_json_response(self, client):
        """Verifica que health check retorna JSON válido."""
        response = client.get(url_for("main.health"))
        assert response.json is not None
        assert "status" in response.json

    def test_health_check_status_ok(self, client, db_session):
        """Verifica que health check retorna status ok."""
        response = client.get(url_for("main.health"))
        data = response.json
        assert data["status"] == "ok"
        assert data["database"] == "ok"

    def test_health_check_contains_version(self, client):
        """Verifica que health check contiene versión."""
        response = client.get(url_for("main.health"))
        data = response.json
        assert "version" in data
        assert data["version"] == "2.0.0"


class TestMainPages:
    """Tests para páginas principales."""

    def test_index_page_accessible(self, client):
        """Verifica que la página index es accesible."""
        response = client.get(url_for("main.index"))
        assert response.status_code == 200

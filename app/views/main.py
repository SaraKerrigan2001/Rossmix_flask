"""Vistas principales (index, test_image, health check)."""
from flask import Blueprint, render_template, jsonify
from app.extensions import cache, db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@cache.cached(timeout=120)
def index():
    return render_template('index.html')


@main_bp.route('/test-image')
@cache.cached(timeout=120)
def test_image():
    return render_template('test_image.html')


@main_bp.route('/health')
def health():
    """
    Health check endpoint para monitoreo de la aplicación.
    Verifica que la aplicación está corriendo y puede conectar a la BD.
    """
    try:
        # Verificar conexión a la base de datos
        db.session.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    status = "ok" if db_status == "ok" else "degraded"
    return jsonify(
        {
            "status": status,
            "database": db_status,
            "version": "2.0.0",
        }
    ), 200 if status == "ok" else 503

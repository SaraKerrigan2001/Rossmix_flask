"""
Punto de entrada de desarrollo — redirige a la aplicación con Blueprints.

Ejecutar:
    python app.py          (desarrollo)
    python run.py          (equivalente)
    gunicorn wsgi:app      (producción)
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True solo en desarrollo — NUNCA en producción
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=5000, debug=debug)

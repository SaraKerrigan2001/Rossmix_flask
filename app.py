"""
Punto de entrada de desarrollo — redirige a la aplicación con Blueprints.

Ejecutar:
    python app.py          (desarrollo)
    python run.py          (equivalente)
    gunicorn wsgi:app      (producción)
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',   # acepta conexiones desde cualquier dispositivo en la red
        port=5000,
        debug=True
    )

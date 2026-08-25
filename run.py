"""
Punto de entrada de la aplicación.
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(debug=debug)

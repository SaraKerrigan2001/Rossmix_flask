"""
Configuración de la aplicación Flask.

Todos los valores sensibles (clave secreta, credenciales de la base de
datos) se leen desde variables de entorno en lugar de estar escritos
directamente en el código. En desarrollo, estas variables se pueden
definir en un archivo ".env" (ver ".env.example") que es cargado
automáticamente por python-dotenv.
"""
import os
from dotenv import load_dotenv

# Carga las variables definidas en un archivo .env (si existe) al entorno
# del proceso. En producción normalmente no hace falta el archivo .env
# porque las variables ya vienen definidas por el sistema/plataforma.
load_dotenv()


def _build_database_uri() -> str:
    """Arma la URI de conexión a PostgreSQL a partir de variables de entorno.

    Permite dos formas de configurarla:
    1. Definiendo DATABASE_URL directamente (útil en plataformas de hosting
       que la proveen de esa forma, ej. Heroku/Render).
    2. Definiendo por separado DB_USER, DB_PASSWORD, DB_HOST, DB_PORT y
       DB_NAME (más cómodo para desarrollo local).
    """
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url

    db_user     = os.environ.get('DB_USER',     'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_host     = os.environ.get('DB_HOST',     'localhost')
    db_port     = os.environ.get('DB_PORT',     '5432')
    db_name     = os.environ.get('DB_NAME',     'Rossmix')

    return (
        f'postgresql+psycopg://{db_user}:{db_password}'
        f'@{db_host}:{db_port}/{db_name}'
    )


class Config:
    # SECRET_KEY debe definirse por variable de entorno. Si no está
    # definida se genera una aleatoria en cada arranque: esto es solo un
    # respaldo para que la app no falle en un entorno mal configurado,
    # pero invalida las sesiones existentes en cada reinicio, así que en
    # producción SIEMPRE se debe definir SECRET_KEY explícitamente.
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()

    SQLALCHEMY_DATABASE_URI    = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de Correo (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@rossmix.com')

    # Configuración de caché
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))

    # Configuración de formularios y CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _build_database_uri() -> str:
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url
    db_user     = os.environ.get('DB_USER',     'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_host     = os.environ.get('DB_HOST',     'localhost')
    db_port     = os.environ.get('DB_PORT',     '5432')
    db_name     = os.environ.get('DB_NAME',     'Rossmix')
    return f'postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'


def _get_secret_key() -> str:
    """Retorna SECRET_KEY o genera una temporal con advertencia."""
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    # Entorno de producción sin clave: error crítico
    if os.environ.get('FLASK_ENV') == 'production':
        print(
            'ERROR CRÍTICO: SECRET_KEY no está definida en producción. '
            'La aplicación se detendrá para evitar exponer sesiones inseguras.',
            file=sys.stderr
        )
        sys.exit(1)
    # Desarrollo: clave aleatoria con advertencia
    print(
        'ADVERTENCIA: SECRET_KEY no definida. '
        'Usando clave aleatoria — las sesiones se invalidarán en cada reinicio. '
        'Define SECRET_KEY en el .env para desarrollo estable.',
        file=sys.stderr
    )
    return os.urandom(32).hex()


class Config:
    SECRET_KEY = _get_secret_key()

    SQLALCHEMY_DATABASE_URI        = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER         = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT           = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS        = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', 'on', '1')
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@rossmix.com')

    CACHE_TYPE            = os.environ.get('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))

    WTF_CSRF_ENABLED    = True
    WTF_CSRF_TIME_LIMIT = None

    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.environ.get('SESSION_LIFETIME_SECONDS', 8 * 60 * 60))
    )

    # ── Subida de archivos ────────────────────────────────────────────────────
    UPLOAD_FOLDER      = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                      'app', 'static', 'uploads', 'perfiles')
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024   # 3 MB máximo
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    # Secure=True solo en producción (requiere HTTPS)
    SESSION_COOKIE_SECURE   = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True    # JS no puede leer la cookie de sesión
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protege contra CSRF cross-site

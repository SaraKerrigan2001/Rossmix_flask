"""
Configuración centralizada de logging para Rossmix.
Evita la duplicación de logs y proporciona consistencia.
"""
import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(app=None, log_level=None):
    """
    Configura el sistema de logging para la aplicación.

    Args:
        app: Instancia de Flask (opcional)
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Determinar nivel de log
    if log_level is None:
        if app and app.debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

    # Crear directorio de logs si no existe
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Formato de logs consistente
    log_format = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s in %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Handler para consola (stderr)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    # Handler para archivo (rotation diaria)
    if not app or app.config.get("FLASK_ENV") != "testing":
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "rossmix.log",
            maxBytes=10485760,  # 10 MB
            backupCount=10,
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)

    # Logger específico para la aplicación
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)

    return app_logger


def get_logger(name):
    """Obtiene un logger específico para un módulo."""
    return logging.getLogger(name)

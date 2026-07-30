"""
Configuración de la aplicación Flask.
"""


class Config:
    SECRET_KEY = 'tu_clave_secreta_aqui_cambiar_en_produccion'

    # Configuración de PostgreSQL - Base de datos Rossmix
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg://postgres:1234@localhost:5432/Rossmix'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

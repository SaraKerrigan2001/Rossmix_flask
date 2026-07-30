"""
Instancias de extensiones Flask.
Se inicializan sin app para evitar importaciones circulares.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

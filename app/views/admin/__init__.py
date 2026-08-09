"""
Blueprint de administración.
Registra todas las rutas del panel de admin.
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Importar los submódulos para registrar las rutas en el blueprint
from app.views.admin import dashboard  # noqa: E402, F401
from app.views.admin import empleados  # noqa: E402, F401
from app.views.admin import servicios  # noqa: E402, F401
from app.views.admin import clientes   # noqa: E402, F401
from app.views.admin import horarios   # noqa: E402, F401
from app.views.admin import citas      # noqa: E402, F401
from app.views.admin import pagos      # noqa: E402, F401
from app.views.admin import exportar   # noqa: E402, F401
from app.views.admin import especialistas  # noqa: E402, F401

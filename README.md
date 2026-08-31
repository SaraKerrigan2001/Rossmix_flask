# Rossmix — Sistema de Agendamiento de Citas
## Salón de Belleza - Plataforma Profesional

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![Flask](https://img.shields.io/badge/flask-2.3-green)
![License](https://img.shields.io/badge/license-MIT-orange)

Sistema web profesional para la gestión de citas, servicios y pagos del Salón de Belleza Rossmix, construido con Flask, PostgreSQL, SQLAlchemy y Docker.

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Arquitectura](#arquitectura)
- [Testing](#testing)
- [Despliegue](#despliegue)
- [CI/CD](#cicd)
- [Seguridad](#seguridad)
- [Documentación](#documentación)

---

## ✨ Características

### Gestión de Citas
- ✅ Agendamiento de citas en 4 pasos
- ✅ Disponibilidad en tiempo real
- ✅ Reprogramación y cancelación
- ✅ Código de reserva único
- ✅ Token de gestión seguro

### Gestión Administrativa
- ✅ Dashboard con estadísticas
- ✅ CRUD de clientes, empleados, servicios
- ✅ Distribución automática de citas
- ✅ Registro de pagos y saldos
- ✅ Reportes en Excel
- ✅ Auditoría de cambios

### Gestión de Usuarios
- ✅ Autenticación segura (hash con Werkzeug)
- ✅ Tres roles: Admin, Especialista, Cliente
- ✅ Autorización granular con decoradores
- ✅ Protección contra fuerza bruta
- ✅ Desactivación de cuentas

### Comunicación
- ✅ Notificaciones internas
- ✅ Envío de emails asíncrono
- ✅ Avisos de citas próximas
- ✅ Recordatorios de pagos

### Seguridad
- ✅ CSRF protection en formularios
- ✅ HTTPONLY y SAMESITE cookies
- ✅ Rate limiting en login
- ✅ SQL Injection prevention (SQLAlchemy)
- ✅ XSS protection (Jinja2)
- ✅ Validación de entrada en backend

---

## 🛠 Tecnologías

### Backend
- **Framework**: Flask 2.3
- **ORM**: SQLAlchemy 2.0
- **Base de datos**: PostgreSQL 16
- **Autenticación**: Werkzeug
- **Validación**: WTForms + email-validator
- **Caching**: Flask-Caching
- **Email**: Flask-Mail
- **Reportes**: ReportLab (PDF), openpyxl (Excel)

### Desarrollo & Testing
- **Testing**: pytest + pytest-flask + pytest-cov
- **Linting**: Ruff
- **Formateo**: Black
- **Pre-commit**: pre-commit
- **CI/CD**: GitHub Actions

### DevOps
- **Containerización**: Docker (multi-stage)
- **Orquestación**: Docker Compose
- **WSGI**: Gunicorn
- **Servidor web**: Puede usarse nginx

---

## 🚀 Instalación

### Requisitos Previos
- Python 3.13+
- PostgreSQL 16+
- Docker & Docker Compose (opcional)
- Git

### Opción 1: Instalación Local

1. **Clonar repositorio**
```bash
git clone https://github.com/SaraKerrigan2001/Rossmix_flask.git
cd Rossmix_flask
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo y testing
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus valores
```

5. **Inicializar base de datos**
```bash
# Crear base de datos PostgreSQL
createdb -U postgres Rossmix

# Ejecutar schema
psql -U postgres -d Rossmix -f scripts/database/Rossmix.sql
```

6. **Ejecutar aplicación**
```bash
python app.py  # Desarrollo
# o
gunicorn wsgi:app  # Producción
```

La aplicación estará disponible en `http://localhost:5000`

### Opción 2: Con Docker Compose

```bash
# Desarrollo
docker-compose up -d

# Producción
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Verificar con: `curl http://localhost:5000/health`

---

## ⚙️ Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura:

```bash
# Seguridad
SECRET_KEY=<clave_muy_segura_y_aleatoria>
FLASK_ENV=development|production|testing

# Base de datos
DB_USER=postgres
DB_PASSWORD=<tu_contraseña>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Rossmix

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=<tu_email>
MAIL_PASSWORD=<tu_app_password>

# Admin inicial
ADMIN_EMAIL=admin@rossmix.com
ADMIN_PASSWORD=<contraseña_segura>
```

### Configuración Detallada

Ver [app/config.py](app/config.py) para todas las opciones disponibles.

---

## 🏗️ Arquitectura

### Patrón MVT + Service Layer

```
HTTP Request
    ↓
Blueprint (Vistas) → Flask Route
    ↓
Validación + Seguridad
    ↓
Service Layer (Lógica de negocio)
    ↓
Models (ORM) ↔ Database
    ↓
JSON/HTML Response
```

### Estructura de Directorios

```
app/
├── __init__.py              # Application Factory
├── config.py                # Configuración centralizada
├── extensions.py            # Extensiones Flask
│
├── models/                  # Modelos SQLAlchemy
│   ├── usuario.py
│   ├── empleado.py
│   ├── servicio.py
│   ├── cita.py
│   ├── pago.py
│   ├── notificacion.py
│   └── ...
│
├── views/                   # Blueprints
│   ├── main.py              # Rutas principales
│   ├── auth.py              # Autenticación
│   ├── citas.py             # Agendamiento
│   └── admin/               # Panel administrativo
│
├── services/                # Lógica de negocio
│   ├── citas_service.py
│   └── reportes_service.py
│
├── forms/                   # Formularios WTForms
├── utils/                   # Utilidades
└── templates/               # Plantillas Jinja2

tests/                       # Suite de pruebas
├── conftest.py              # Fixtures compartidas
├── test_auth.py
├── test_models.py
└── ...
```

### Roles de Usuario

| Rol | Permisos | Acceso |
|-----|----------|--------|
| **Admin** | Completo | Panel administrativo, CRUD, reportes, auditoría |
| **Especialista** | Limitado | Portal propio, ver citas asignadas, mis citas |
| **Cliente** | Mínimo | Agendar citas, ver historial, descargar PDF |

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo tests de autenticación
pytest -m auth

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/test_auth.py::TestLogin::test_login_valid_credentials
```

### Estructura de Tests

```
tests/
├── conftest.py              # Fixtures globales
├── test_auth.py             # Autenticación
├── test_models.py           # Modelos
├── test_main.py             # Rutas principales
└── ...
```

### Fixtures Disponibles

- `client` — Cliente de prueba Flask
- `app_context` — Contexto de aplicación
- `db_session` — Base de datos limpia por test
- `admin_user` — Usuario admin
- `cliente_user` — Usuario cliente
- `admin_logged_in` — Admin con sesión iniciada

### Escribir Nuevas Pruebas

```python
@pytest.mark.auth
def test_login_valid_credentials(client, admin_user):
    """Prueba login con credenciales válidas."""
    response = client.post(
        url_for("auth.login"),
        data={"email": "admin@test.com", "password": "admin123"}
    )
    assert response.status_code == 302  # Redirect
```

---

## 🐳 Despliegue

### Con Docker (Recomendado)

1. **Build image**
```bash
docker build -t rossmix:latest .
```

2. **Run con Docker Compose**
```bash
docker-compose up -d
```

3. **Verificar**
```bash
curl http://localhost:5000/health
# {"status": "ok", "database": "ok", "version": "2.0.0"}
```

### Con Gunicorn (Linux/Mac)

```bash
gunicorn \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --bind 0.0.0.0:5000 \
  wsgi:app
```

### En Producción

1. Usar HTTPS (certificado SSL/TLS)
2. Definir `FLASK_ENV=production`
3. Generar `SECRET_KEY` aleatorio y seguro
4. Usar PostgreSQL en servidor dedicado
5. Configurar backups automáticos de BD
6. Habilitar logs persistentes

---

## 🔄 CI/CD

### GitHub Actions

Los workflows se ejecutan automáticamente en cada push y pull request:

- **[tests.yml](.github/workflows/tests.yml)** — Ejecuta pytest y verifica cobertura
- **[docker.yml](.github/workflows/docker.yml)** — Verifica que Docker build funcione

### Ejecutar Localmente

```bash
# Instalar pre-commit hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files

# Pre-commit hooks se ejecutarán automáticamente antes de cada commit
```

---

## 🔒 Seguridad

### Implementado

✅ **Autenticación**
- Hash seguro de contraseñas (Werkzeug.pbkdf2)
- Rate limiting (10 intentos / 30 min)
- Sesiones con HTTPONLY + SAMESITE

✅ **Autorización**
- Decoradores `@admin_required`, `@especialista_required`
- Validación en backend (no confiar en frontend)
- Auditoría de acciones críticas

✅ **CSRF**
- Protección habilitada (WTF_CSRF_ENABLED)
- Tokens en formularios

✅ **SQL Injection**
- SQLAlchemy con parámetros (no concatenación)
- Prepared statements

✅ **XSS**
- Escaping en Jinja2
- `|safe` solo donde es necesario

✅ **Headers de Seguridad**
- `Secure` cookie flag en producción
- `HttpOnly` en todas las cookies
- `SameSite=Lax` contra CSRF cross-site

### Checklist de Seguridad

- [ ] `SECRET_KEY` definida en variables de entorno
- [ ] HTTPS habilitado en producción
- [ ] Contraseña `ADMIN_PASSWORD` segura
- [ ] Base de datos con usuario limitado
- [ ] Logs no contienen contraseñas/tokens
- [ ] `.env` excluido de repositorio
- [ ] Backups encriptados

---

## 📝 Documentación

### Documentos Incluidos

- [docs/MANUAL_TECNICO.md](docs/MANUAL_TECNICO.md) — Arquitectura y componentes
- [docs/MANUAL_USUARIO.md](docs/MANUAL_USUARIO.md) — Guía de usuario
- [docs/RELACIONES_BD_ROSSMIX.md](docs/RELACIONES_BD_ROSSMIX.md) — Esquema de BD
- [docs/CONFIGURACION_FINAL.md](docs/CONFIGURACION_FINAL.md) — Setup completo

### Generar Documentación

```bash
# HTML de casos de prueba
python scripts/database/generar_casos_html.py

# Excel con diagrama BD
python scripts/utilidades/generar_excel_completo.py
```

---

## 🔧 Desarrollo

### Pre-requisitos de Desarrollo

```bash
pip install -r requirements-dev.txt
```

### Herramientas

```bash
# Linting
ruff check .

# Formateo
black .

# Tests
pytest --cov=app

# Pre-commit
pre-commit install
pre-commit run --all-files
```

### Agregar Dependencias

```bash
pip install <paquete>
pip freeze > requirements.txt
```

---

## 🐛 Troubleshooting

### "ERROR: no se puede conectar a PostgreSQL"

```bash
# Verificar que PostgreSQL está corriendo
sudo service postgresql status

# O con Docker
docker-compose ps
```

### "SECRET_KEY no definida en producción"

```bash
# Generar clave segura
python -c "import os; print(os.urandom(32).hex())"

# Agregara .env
echo "SECRET_KEY=<la_clave>" >> .env
```

### "CSRF token missing"

```python
# En formularios, incluir:
{{ form.hidden_tag() }}  # O
{{ form.csrf_token }}
```

### "IntegrityError en BD"

```bash
# Recrear BD
dropdb -U postgres Rossmix
createdb -U postgres Rossmix
psql -U postgres -d Rossmix -f scripts/database/Rossmix.sql
```

---

## 📊 Health Check

```bash
curl http://localhost:5000/health

# Respuesta esperada:
{
  "status": "ok",
  "database": "ok",
  "version": "2.0.0"
}
```

---

## 📄 Licencia

MIT License — Ver [LICENSE](LICENSE) para detalles.

---

## 👥 Autores

- **Sara Kerrigan** — Desarrollo Principal
- Rossmix Team — Contribuciones

---

## 📞 Contacto

- Email: dev@rossmix.com
- GitHub: [SaraKerrigan2001/Rossmix_flask](https://github.com/SaraKerrigan2001/Rossmix_flask)
- Issues: [GitHub Issues](https://github.com/SaraKerrigan2001/Rossmix_flask/issues)

---

**Última actualización**: Agosto 2026 | Versión 2.0.0

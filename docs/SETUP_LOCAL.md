# Setup Local - Guía de Desarrollo

## 🚀 Inicio Rápido (5 minutos)

### 1. Clonar Repositorio

```bash
git clone https://github.com/SaraKerrigan2001/Rossmix_flask.git
cd Rossmix_flask
```

### 2. Crear Entorno Virtual

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Configurar Variables de Entorno

```bash
cp .env.example .env
# Editar .env con tus valores
```

**Valores mínimos necesarios:**
```env
SECRET_KEY=<clave_aleatoria_muy_segura>
DB_USER=postgres
DB_PASSWORD=<tu_contraseña>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Rossmix
ADMIN_PASSWORD=admin123
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=<tu_email>
MAIL_PASSWORD=<app_password_gmail>
```

### 5. Inicializar Base de Datos

**Opción A: PostgreSQL Local**

```bash
# Crear base de datos
createdb -U postgres Rossmix

# Ejecutar schema
psql -U postgres -d Rossmix -f scripts/database/Rossmix.sql
```

**Opción B: Docker Compose (Recomendado)**

```bash
docker-compose up -d
```

Esperar a que PostgreSQL esté listo (10-15 segundos), luego:
```bash
docker-compose exec web flask db upgrade  # Si existe Alembic
# O manualmente:
docker-compose exec db psql -U postgres -d Rossmix -f /docker-entrypoint-initdb.d/01_schema.sql
```

### 6. Ejecutar la Aplicación

```bash
python app.py
```

Acceder a: `http://localhost:5000`

**Credenciales de prueba:**
- Email: `admin@rossmix.com`
- Contraseña: `admin123` (definida en `ADMIN_PASSWORD` del `.env`)

---

## 🧪 Testing

### Ejecutar Todos los Tests

```bash
pytest
```

### Con Cobertura

```bash
pytest --cov=app --cov-report=html
# Abrir htmlcov/index.html en navegador
```

### Tests Específicos

```bash
# Solo autenticación
pytest -m auth

# Solo modelos
pytest -m models

# Un archivo específico
pytest tests/test_auth.py

# Una función específica
pytest tests/test_auth.py::TestLogin::test_login_valid_credentials -v
```

---

## 🔧 Herramientas de Desarrollo

### Linting y Formato

```bash
# Revisar linting (sin cambios)
ruff check .

# Arreglar problemas automáticos
ruff check --fix .

# Formateo de código
black .

# Verificar sin cambiar
black --check .
```

### Pre-commit Hooks

```bash
# Instalar hooks (una sola vez)
pre-commit install

# Ejecutar manualmente en todos los archivos
pre-commit run --all-files

# Ejecutar en archivos staged
pre-commit run
```

Los hooks se ejecutarán automáticamente antes de cada commit.

---

## 📊 Estructura de Pruebas

```
tests/
├── conftest.py              # Fixtures globales
├── test_auth.py             # Tests de autenticación
├── test_models.py           # Tests de modelos
├── test_main.py             # Tests de rutas principales
└── services/
    └── test_citas_service.py
```

### Crear Nuevo Test

1. Crear archivo `tests/test_<modulo>.py`
2. Importar fixtures: `from tests.conftest import client, admin_user, etc`
3. Usar decorador `@pytest.mark.<categoria>`

```python
@pytest.mark.auth
def test_example(client, admin_user):
    response = client.get('/ruta')
    assert response.status_code == 200
```

---

## 🐳 Con Docker Compose

### Desarrollo

```bash
docker-compose up -d
```

- App: `http://localhost:5000`
- PostgreSQL: `localhost:5432`

### Producción

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Logs

```bash
docker-compose logs -f web
docker-compose logs -f db
```

### Detener

```bash
docker-compose down
```

### Eliminar Volúmenes (CUIDADO: Borra BD)

```bash
docker-compose down -v
```

---

## 🔒 Configuración de Seguridad

### Generar SECRET_KEY Seguro

```bash
python -c "import os; print(os.urandom(32).hex())"
```

Copiar en `.env`:
```env
SECRET_KEY=<el_valor_generado>
```

### Configurar Email (Gmail)

1. Habilitar "Contraseñas de aplicación" en Google Account
2. Copiar en `.env`:
```env
MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=<app_password_de_16_caracteres>
```

---

## 🚨 Troubleshooting

### "No se puede conectar a PostgreSQL"

```bash
# Verificar que PostgreSQL está corriendo
sudo service postgresql status

# O con Docker
docker-compose ps
docker-compose logs db
```

### "SECRET_KEY no definida"

```bash
# Generar y agregar al .env
python -c "import os; print('SECRET_KEY=' + os.urandom(32).hex())" >> .env
```

### "ModuleNotFoundError: No module named 'app'"

```bash
# Asegurarse de estar en el directorio correcto
cd Rossmix_flask

# Activar entorno virtual
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

### "CSRF token missing"

- Asegurarse de que los formularios incluyen `{{ form.hidden_tag() }}`
- Reiniciar el servidor

### "IntegrityError en BD"

```bash
# Recrear BD
dropdb -U postgres Rossmix
createdb -U postgres Rossmix
psql -U postgres -d Rossmix -f scripts/database/Rossmix.sql
```

---

## 📝 Workflow Típico

### Agregar Nueva Funcionalidad

1. **Crear rama de feature**
```bash
git checkout -b feature/nueva-funcionalidad
```

2. **Hacer cambios y tests**
```bash
# Editar código
# Crear tests en tests/test_*.py
```

3. **Ejecutar tests y lint**
```bash
pytest
ruff check --fix .
black .
pre-commit run --all-files
```

4. **Commit**
```bash
git add .
git commit -m "feat: descripción de la funcionalidad"
```

5. **Push y Pull Request**
```bash
git push origin feature/nueva-funcionalidad
# Crear PR en GitHub
```

---

## 🎯 Checklist Antes de Producción

- [ ] Todos los tests pasando (`pytest`)
- [ ] Cobertura >80% (`pytest --cov=app`)
- [ ] Lint aprobado (`ruff check .`)
- [ ] Código formateado (`black .`)
- [ ] SECRET_KEY único y seguro
- [ ] DATABASE_URL correcta
- [ ] MAIL_USERNAME y MAIL_PASSWORD configurados
- [ ] ADMIN_PASSWORD fuerte
- [ ] `.env` NO incluido en Git
- [ ] HTTPS habilitado
- [ ] FLASK_ENV=production

---

## 📚 Documentación Adicional

- [README.md](../README.md) — Visión general del proyecto
- [docs/MANUAL_TECNICO.md](../docs/MANUAL_TECNICO.md) — Arquitectura detallada
- [docs/RELACIONES_BD_ROSSMIX.md](../docs/RELACIONES_BD_ROSSMIX.md) — Esquema de BD

---

**Última actualización**: Agosto 2026 | Versión 2.0.0

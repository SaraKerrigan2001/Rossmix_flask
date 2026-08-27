# Manual Técnico - Rossmix

Este documento describe la arquitectura, la pila tecnológica y las reglas de negocio implementadas en el desarrollo de la aplicación web **Rossmix**. Está dirigido a desarrolladores y administradores de sistemas responsables de mantener y escalar la plataforma.

---

## 1. Arquitectura y Pila Tecnológica

La aplicación está construida bajo un patrón **MVT (Model-View-Template)** utilizando tecnologías modernas tanto en el Backend como en el Frontend.

### Backend
- **Framework Principal:** Flask (Python).
- **ORM:** Flask-SQLAlchemy (para la gestión de base de datos relacional).
- **Migraciones:** Flask-Migrate (Alembic) para el control de versiones del esquema de base de datos.
- **Autenticación:** Gestión de sesiones segura en servidor (`flask.session`) y hash criptográfico de contraseñas con Werkzeug.
- **Estructura Modular:** Uso de **Flask Blueprints** para separar lógicamente la aplicación en módulos (Auth, Cliente, Especialista, Admin, Citas, Main, Notificaciones).

### Frontend
- **Templates:** Jinja2 (Motor de plantillas nativo de Flask) con herencia desde `base.html`.
- **Estilos (CSS):** CSS Vainilla enfocado en diseño moderno, paleta de colores oficial unificada (Rosa `#C41E3A` y `#FFF0F6`), y diseño responsivo (`media queries`).
- **Lógica de UI:** JavaScript puro (Vanilla JS) para micro-interacciones, modales, y AJAX nativo (`fetch API`) en casos necesarios.
- **Iconografía:** Bootstrap Icons (vía CDN).

### Base de Datos y Despliegue
- **Base de Datos:** PostgreSQL 16 (Producción) / SQLite (Opcional en desarrollo local muy básico, aunque se prioriza PostgreSQL).
- **Contenedorización:** Docker y Docker Compose para garantizar consistencia entre el entorno de desarrollo y producción. La app corre sobre un servidor WSGI (Gunicorn en producción).

---

## 2. Estructura del Proyecto

El código fuente está estructurado de la siguiente manera:

```text
Rossmix_flask/
│
├── app/                      # Código fuente de la aplicación Flask
│   ├── models/               # Modelos de base de datos SQLAlchemy
│   ├── templates/            # Vistas en HTML (Jinja2)
│   ├── static/               # CSS, JS, Imágenes y fuentes
│   ├── views/                # Blueprints (Controladores)
│   ├── __init__.py           # Inicialización de la app (Factory Pattern)
│   └── extensions.py         # Instancias globales (db, migrate, etc.)
│
├── docs/                     # Documentación técnica, diagramas y manuales
├── scripts/                  # Scripts utilitarios (Seeds de base de datos, utilidades, etc.)
├── .env                      # Variables de entorno (Secret Key, DB URI)
├── docker-compose.yml        # Orquestación de contenedores (app + bd)
├── Dockerfile                # Receta de construcción de la imagen web
├── requirements.txt          # Dependencias de Python
└── run.py / wsgi.py          # Puntos de entrada para el servidor
```

---

## 3. Reglas de Negocio Implementadas

### Reglas de Arquitectura MVT
1. **Skinny Controllers / Fat Models:** 
   - Las validaciones primarias y cálculos automáticos (ej. cálculo de saldo de una cita) se realizan en propiedades o métodos dentro de `app/models/`.
   - Las vistas (Blueprints en `app/views/`) actúan como controladores delgados, manejando solo el ciclo HTTP (recepción de datos, invocación al modelo, renderizado del template).
2. **Contexto de Aplicación:**
   - Para evitar dependencias circulares, la instancia `db` se importa desde `app.extensions`.
   - Se utiliza `current_app` para acceder a configuraciones globales dentro de los Blueprints.

### Reglas de Citas y Pagos (Core Logic)
- **Fechas Futuras:** La lógica del backend impide registrar citas en fechas u horas pasadas.
- **Abono Mínimo Obligatorio:** Constantemente evaluado al registrar una nueva cita ($5,000 COP).
- **Cancelación:** La función de cancelación en el backend valida el `datetime` actual contra el `datetime` de la cita; si faltan menos de 2 horas, la operación lanza un error y es abortada.
- **Triggers Lógicos de Pago:** Cuando un administrador confirma un pago, el sistema llama internamente a métodos que recalculan el `saldo_pendiente` de la cita y actualizan automáticamente el estado a `completada` si el saldo es `$0`.

---

## 4. Control de Transacciones de Base de Datos

En PostgreSQL, cualquier error en una consulta invalida la transacción actual. Por ello, todas las operaciones de escritura/actualización en el código están estructuradas así:

```python
try:
    nuevo_registro = Entidad(...)
    db.session.add(nuevo_registro)
    db.session.commit()
except Exception as e:
    db.session.rollback()  # <- Crítico para liberar el estado de error en PostgreSQL
    current_app.logger.error(f"Error en BD: {str(e)}")
    flash("Error al procesar la solicitud", "error")
```

---

## 5. Instrucciones de Despliegue (Docker)

El flujo estándar para arrancar el entorno usando contenedores es:

1. Clonar el repositorio y copiar `.env.example` a `.env`. Configurar contraseñas.
2. Construir e iniciar los servicios en segundo plano:
   ```bash
   docker-compose build
   docker-compose up -d
   ```
3. Ejecutar las migraciones de BD o los scripts de *seeding* (si es la primera vez):
   ```bash
   docker-compose run --rm web flask db upgrade
   docker-compose --profile seed up seed
   ```

El contenedor expone por defecto el puerto 5000 (o el configurado en `.env`), donde Gunicorn recibe las peticiones. En un ambiente productivo, se recomienda usar Nginx o Cloudflare Tunnels (el proyecto incluye un `cloudflared.exe`) como proxy inverso.

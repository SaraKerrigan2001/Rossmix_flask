# Rossmix — Sistema de Agendamiento de Citas

Sistema web para la gestión de citas y servicios del **Salón de Belleza Rossmix**, construido con Flask, PostgreSQL y SQLAlchemy.

---

## Estructura del Proyecto

```
Rossmix_flask/
├── app/
│   ├── __init__.py              # Application Factory (blueprints, extensiones, admin inicial)
│   ├── config.py                # Configuración central (leída desde variables de entorno)
│   ├── extensions.py            # Instancias de db, mail, cache, csrf
│   │
│   ├── models/                  # Modelos ORM (SQLAlchemy)
│   │   ├── usuario.py           # Cliente, Admin y Especialista (tabla unificada)
│   │   ├── empleado.py          # Empleados del salón con lógica de negocio
│   │   ├── servicio.py          # Servicios y relación Empleado-Servicio (M2M)
│   │   ├── horario.py           # Horarios de trabajo por empleado y día
│   │   ├── cita.py              # Citas con estados, código de reserva y token de gestión
│   │   ├── pago.py              # Pagos vinculados a citas
│   │   ├── notificacion.py      # Notificaciones internas + email asíncrono
│   │   └── configuracion.py     # Parámetros configurables del sistema (clave-valor)
│   │
│   ├── views/                   # Blueprints (controladores)
│   │   ├── main.py              # Página principal e inicio
│   │   ├── auth.py              # Login, registro y logout
│   │   ├── cliente.py           # Dashboard del cliente
│   │   ├── citas.py             # Flujo de agendamiento (4 pasos), reprogramación y pagos
│   │   ├── notificaciones.py    # Centro de notificaciones
│   │   ├── especialista.py      # Portal de especialistas
│   │   └── admin/               # Panel de administración
│   │       ├── dashboard.py     # Estadísticas y agenda diaria
│   │       ├── citas.py         # Gestión, asignación y distribución de citas
│   │       ├── clientes.py      # CRUD de clientes
│   │       ├── empleados.py     # CRUD de empleados
│   │       ├── especialistas.py # Gestión de cuentas de especialista
│   │       ├── servicios.py     # CRUD de servicios
│   │       ├── horarios.py      # CRUD de horarios
│   │       ├── pagos.py         # Registro y confirmación de pagos
│   │       └── exportar.py      # Exportación a Excel
│   │
│   ├── services/                # Capa de lógica de negocio
│   │   ├── citas_service.py     # Validación de disponibilidad, creación de citas y tokens
│   │   └── reportes_service.py  # Generación de reportes Excel por tipo y período
│   │
│   ├── forms/                   # Formularios WTForms con CSRF
│   │   ├── auth.py              # Login, registro y pago
│   │   └── citas.py             # Selección de horario y confirmación de cita
│   │
│   ├── utils/
│   │   ├── decorators.py        # admin_required, especialista_required, login_required
│   │   └── helpers.py           # add_notificacion (BD + email asíncrono), context processor
│   │
│   ├── static/
│   │   ├── style.css
│   │   └── images/              # Imágenes de servicios y galería
│   │
│   └── templates/               # Plantillas Jinja2
│       ├── base.html            # Layout base con navbar y notificaciones
│       ├── login.html / registro.html / index.html
│       ├── dashboard_cliente.html / dashboard_admin.html
│       ├── citas/               # Pasos 1-4 del agendamiento, mis citas, pagos, PDF
│       ├── especialista/        # Dashboard, citas disponibles, mis citas
│       └── admin/               # Todas las vistas del panel de administración
│
├── scripts/
│   └── database/
│       └── Rossmix.sql          # Esquema completo PostgreSQL con datos semilla
│
├── app.py                       # Punto de entrada (desarrollo)
├── wsgi.py                      # Punto de entrada (producción / Gunicorn)
├── Procfile                     # Configuración Heroku/Render
├── requirements.txt             # Dependencias Python
└── .env.example                 # Plantilla de variables de entorno
```

---

## Roles de Usuario

| Rol | Acceso |
|---|---|
| `admin` | Panel completo: citas, clientes, empleados, servicios, horarios, pagos, reportes |
| `especialista` | Portal propio: ver citas disponibles, aceptarlas y gestionar su agenda |
| `cliente` | Agendar citas en 4 pasos, ver historial, descargar PDF, reprogramar y cancelar |

---

## Flujo de Agendamiento

1. **Paso 1** — Seleccionar servicio
2. **Paso 2** — Elegir especialista (o asignación aleatoria)
3. **Paso 3** — Seleccionar fecha y hora disponible
4. **Paso 4** — Confirmar y registrar abono mínimo ($5.000 COP)

---

## Base de Datos

Esquema PostgreSQL en `scripts/database/Rossmix.sql`. Incluye:
- 9 tablas, 2 tipos ENUM, 2 vistas, índices de rendimiento y datos semilla
- Para inicializar: ejecutar el SQL en pgAdmin sobre la BD `Rossmix`

---

## Configuración

1. Copiar `.env.example` a `.env` y completar los valores
2. Asegurarse de definir `ADMIN_PASSWORD` para que se cree el usuario administrador inicial
3. Ejecutar `Rossmix.sql` en PostgreSQL
4. Iniciar: `python app.py` (desarrollo) o `gunicorn wsgi:app` (producción)

---

## Dependencias Principales

- Flask 2.3 + SQLAlchemy + psycopg 3
- Flask-WTF (CSRF), Flask-Mail, Flask-Caching
- ReportLab (PDF), openpyxl (Excel)
- Gunicorn (producción)

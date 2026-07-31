# Estructura del Proyecto Rossmix Flask

El proyecto tiene **dos formas de ejecutarse**, ambas funcionales y conectadas a la misma base de datos PostgreSQL:

| Modo | Archivo de entrada | Arquitectura |
|------|--------------------|--------------|
| **Activo actualmente** | `python app.py` | Monolítico (todo en un archivo) |
| Alternativo | `python run.py` | MVT con Blueprints en `app/` |

---

## Estructura de Directorios

```
Rossmix_flask/
│
├── app.py                       # ★ PUNTO DE ENTRADA ACTIVO (monolítico)
│                                #   Contiene modelos, rutas y lógica en un solo archivo.
│                                #   Usa template_folder y static_folder apuntando a app/
│
├── run.py                       # Punto de entrada alternativo (Blueprints)
│                                #   Llama a create_app() definido en app/__init__.py
│
├── requirements.txt             # Dependencias del proyecto:
│                                #   Flask, Flask-SQLAlchemy, Werkzeug, psycopg, openpyxl
│
├── crear_usuarios.py            # Script para poblar usuarios de prueba en PostgreSQL
├── estructura_proyecto.md       # Este archivo
│
├── app/                         # Carpeta de la aplicación (usada por ambos modos)
│   │
│   ├── __init__.py              # Factory create_app() — usado solo por run.py
│   ├── config.py                # Configuración: PostgreSQL URI, SECRET_KEY
│   ├── extensions.py            # Instancia compartida de SQLAlchemy (db)
│   │
│   ├── models/                  # Modelos SQLAlchemy (usados por run.py)
│   │   ├── __init__.py
│   │   ├── usuario.py           # Modelo Usuario (clientes y administradores)
│   │   ├── servicio.py          # Modelo Servicio + tabla intermedia EmpleadoServicio
│   │   ├── empleado.py          # Modelo Empleado
│   │   ├── horario.py           # Modelo HorarioEmpleado
│   │   ├── cita.py              # Modelo Cita
│   │   ├── pago.py              # Modelo Pago
│   │   └── notificacion.py      # Modelo Notificacion
│   │
│   ├── views/                   # Blueprints de rutas (usados solo por run.py)
│   │   ├── __init__.py          # Registro y exportación de todos los Blueprints
│   │   ├── auth.py              # Login, Registro, Logout
│   │   ├── citas.py             # Flujo de agendamiento (pasos 1–4), cancelación
│   │   ├── cliente.py           # Dashboard del cliente
│   │   ├── main.py              # Index, test_image
│   │   ├── notificaciones.py    # Lectura y marcado de notificaciones
│   │   └── admin/               # Sub-blueprints del panel administrador
│   │       ├── __init__.py
│   │       ├── dashboard.py     # Estadísticas del admin
│   │       ├── citas.py         # Listado y cambio de estado de citas
│   │       ├── clientes.py      # CRUD de clientes
│   │       ├── empleados.py     # CRUD de empleados + asignación de servicios
│   │       ├── horarios.py      # Configuración de horarios por empleado
│   │       ├── servicios.py     # CRUD de servicios
│   │       ├── pagos.py         # Registro y reembolso de pagos
│   │       └── exportar.py      # Exportación a Excel (.xlsx)
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py        # @admin_required
│   │   └── helpers.py           # add_notificacion(), inject_notificaciones()
│   │
│   ├── templates/               # ★ Templates HTML compartidos por ambos modos
│   │   ├── base.html            # Layout maestro (navbar, flash messages, footer)
│   │   ├── index.html           # Página de inicio (landing del salón)
│   │   ├── login.html           # Inicio de sesión
│   │   ├── registro.html        # Registro de clientes
│   │   ├── dashboard_admin.html # Panel del administrador
│   │   ├── dashboard_cliente.html
│   │   ├── notificaciones.html
│   │   ├── test_image.html
│   │   ├── citas/               # Flujo de agendamiento (4 pasos)
│   │   │   ├── paso1_servicio.html
│   │   │   ├── paso2_empleado.html
│   │   │   ├── paso3_fecha_hora.html
│   │   │   ├── paso4_confirmacion.html
│   │   │   ├── confirmada.html
│   │   │   ├── mis_citas.html
│   │   │   └── cliente_pagos_form.html
│   │   └── admin/               # Plantillas del panel admin
│   │       ├── citas.html
│   │       ├── clientes.html
│   │       ├── clientes_form.html
│   │       ├── empleados.html
│   │       ├── empleados_form.html
│   │       ├── horarios.html
│   │       ├── horarios_form.html
│   │       ├── pagos.html
│   │       ├── pagos_form.html
│   │       ├── servicios.html
│   │       └── servicios_form.html
│   │
│   └── static/                  # ★ Archivos estáticos compartidos por ambos modos
│       ├── style.css
│       └── images/
│           └── salon.jpeg
│
└── docs/                        # Documentación adicional del proyecto
```

---

## Cómo Arrancar la Aplicación

### Modo activo (monolítico)
```bash
python app.py
```
Levanta el servidor en `http://127.0.0.1:5000`

### Modo alternativo (Blueprints)
```bash
python run.py
```

---

## Credenciales de Prueba

| Rol | Email | Contraseña |
|-----|-------|------------|
| Administrador | admin@rossmix.com | admin123 |

---

## Rutas Principales

| Ruta | Descripción |
|------|-------------|
| `/` | Página de inicio |
| `/login` | Iniciar sesión |
| `/registro` | Crear cuenta |
| `/dashboard/cliente` | Panel del cliente |
| `/dashboard/admin` | Panel del administrador |
| `/citas/agendar/paso1` | Iniciar agendamiento |
| `/citas/mis-citas` | Ver citas del cliente |
| `/admin/citas` | Gestión de citas (admin) |
| `/admin/empleados` | Gestión de empleados |
| `/admin/servicios` | Gestión de servicios |
| `/admin/horarios` | Configuración de horarios |
| `/admin/pagos` | Gestión de pagos |
| `/admin/exportar/<tipo>/<periodo>` | Exportar a Excel |

# Rossmix_flask

# MediQQTA - Sistema de Agendamiento de Citas

Este proyecto es un sistema de agendamiento estructurado bajo el patrón MVT/MVC en Flask utilizando una capa de servicios (`services/`) para aislar la lógica de negocio.

## Estructura del Proyecto

La estructura actual implementada es la siguiente:
```
MediQQTA/
├── agendamiento/                 # Aplicación principal
│   ├── __init__.py               # Inicialización y registro de vistas (Blueprints)
│   ├── apps.py                   # Configuración del módulo de agendamiento
│   ├── admin.py                  # Rutas y configuración de administración
│   ├── urls.py                   # Enrutamiento dinámico general
│   │
│   ├── models/                   # 🗄️ MODELOS
│   │   ├── __init__.py           # Re-exportación de todos los modelos
│   │   ├── usuarios.py           # Modelos de Usuario y Rol
│   │   ├── pacientes.py          # Modelos de Paciente y Entidad (Aseguradora)
│   │   ├── citas.py              # Modelos de Cita y Bloqueo de Agenda
│   │   └── configuracion.py      # Modelos de Configuración y Auditoría
│   │
│   ├── views/                    # 🎮 CONTROLADORES
│   │   ├── __init__.py           # Registro e importación de controladores
│   │   ├── auth_views.py         # Login y Logout
│   │   ├── dashboard_views.py    # Estadísticas e interfaz principal
│   │   ├── citas_views.py        # Agendar, cancelar y reprogramar citas
│   │   ├── pacientes_views.py    # CRUD de pacientes
│   │   └── config_views.py       # Configuración del sistema y reportes
│   │
│   ├── services/                 # ⚙️ LÓGICA DE NEGOCIO (Service Layer)
│   │   ├── __init__.py           # Exportación de servicios
│   │   ├── citas_service.py      # Validación de disponibilidad y bloqueos
│   │   └── reportes_service.py   # Creación de PDFs y reportes en Excel
│   │
│   └── templates/                # 🎨 VISTAS / INTERFAZ
│       └── agendamiento/         # Templates organizados por la aplicación
│           ├── base.html         # Plantilla base
│           ├── login.html        # Formulario de inicio de sesión
│           ├── dashboard.html    # Panel de control principal
│           ├── citas.html        # Listado y agenda de citas
│           └── pacientes.html    # Gestión de pacientes
│
├── config.py                     # Configuración del servidor Flask
├── run.py                        # Punto de entrada de la aplicación
└── requirements.txt              # Dependencias de Python
```

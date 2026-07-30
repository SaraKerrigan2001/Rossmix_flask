# Estructura del Proyecto Rossmix Flask (MVT)

Esta es la estructura de directorios y archivos implementada tras la refactorización a MVT (Model-View-Template) utilizando Blueprints en Flask.

```
Rossmix_flask/
│
├── app/                         # Carpeta principal de la aplicación
│   ├── __init__.py              # Factory de la aplicación Flask: create_app()
│   ├── config.py                # Configuración de variables (PostgreSQL URI, SECRET_KEY)
│   ├── extensions.py            # Instancia compartida de SQLAlchemy (db)
│   │
│   ├── models/                  # [M] MODELOS (Estructura de Base de Datos con SQLAlchemy)
│   │   ├── __init__.py          # Exportación unificada de todos los modelos
│   │   ├── cita.py              # Modelo de Citas
│   │   ├── empleado.py          # Modelo de Empleados
│   │   ├── horario.py           # Modelo de Horarios de Trabajo de Empleados
│   │   ├── notificacion.py      # Modelo de Notificaciones para Usuarios
│   │   ├── pago.py              # Modelo de Pagos registrados
│   │   ├── servicio.py          # Modelo de Servicios y relación de servicios por empleado
│   │   └── usuario.py           # Modelo de Usuarios (Clientes y Administradores)
│   │
│   ├── views/                   # [V] VISTAS (Lógica de Rutas / Controladores mediante Blueprints)
│   │   ├── __init__.py          # Inicialización y exportación de Blueprints
│   │   ├── auth.py              # Autenticación: Login, Registro y Logout
│   │   ├── citas.py             # Lógica de reserva, cancelación e historial de citas
│   │   ├── cliente.py           # Vistas del dashboard de clientes
│   │   ├── main.py              # Vistas principales de landing y pruebas generales
│   │   ├── notificaciones.py    # Gestión de lectura de notificaciones (API)
│   │   │
│   │   └── admin/               # Panel de Administración (Sub-rutas con prefix '/admin')
│   │       ├── __init__.py      # Registro del Blueprint de Admin y decorador @admin_required
│   │       ├── citas.py         # Listado, filtros y estados de citas para admin
│   │       ├── clientes.py      # CRUD de clientes y estadísticas
│   │       ├── dashboard.py     # Estadísticas principales del administrador
│   │       ├── empleados.py     # CRUD de empleados y asignación de servicios
│   │       ├── exportar.py      # Exportación de datos (Citas/Pagos) a Excel (.xlsx)
│   │       ├── horarios.py      # Configuración de horarios por empleado
│   │       ├── pagos.py         # Registro y devolución de pagos de clientes
│   │       └── servicios.py     # CRUD de servicios de salón
│   │
│   ├── utils/                   # Herramientas Auxiliares / Utilidades
│   │   ├── __init__.py          # Exportación de decoradores y ayudantes
│   │   ├── decorators.py        # Decoradores personalizados (@admin_required)
│   │   └── helpers.py           # Ayudantes (add_notificacion, context_processors)
│   │
│   ├── templates/               # [T] TEMPLATES (HTML estructurado con Jinja2)
│   │   ├── base.html            # Layout maestro común a todas las páginas
│   │   ├── index.html           # Página de inicio
│   │   ├── login.html           # Página de inicio de sesión
│   │   ├── registro.html        # Formulario de registro de clientes
│   │   ├── dashboard_admin.html # Interfaz del dashboard admin
│   │   ├── dashboard_cliente.html# Interfaz del dashboard cliente
│   │   ├── notificaciones.html  # Bandeja de notificaciones del usuario
│   │   ├── test_image.html      # Página de pruebas de imágenes
│   │   ├── admin/               # Plantillas exclusivas del administrador (CRUDs)
│   │   └── citas/               # Plantillas del flujo de reserva del cliente
│   │
│   └── static/                  # Recurso Estáticos (Frontend)
│       ├── style.css            # Estilos CSS generales
│       └── images/              # Logo, fotos y recursos visuales
│
├── scripts/                     # Scripts complementarios de base de datos
│   ├── database/
│   │   └── Rossmix.sql          # Esquema original de la base de datos SQL
│   └── fix_price.py             # Script de corrección rápida de precios
│
├── crear_usuarios.py            # Script independiente para poblar usuarios de prueba en PostgreSQL
├── requirements.txt             # Librerías de Python requeridas para el entorno
├── app.py.bak                   # Respaldo del archivo app.py original (monolítico)
└── run.py                       # Punto de inicio para arrancar el servidor web
```

---

## Cómo Arrancar la Aplicación
1. Asegúrate de tener las dependencias instaladas:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la aplicación usando el nuevo punto de entrada:
   ```bash
   python run.py
   ```

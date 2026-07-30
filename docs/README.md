# 💅 Rossmix - Sistema de Gestión de Salón de Belleza

Sistema web para gestionar citas en el salón de belleza Rossmix.

## 🚀 Instalación

1. Asegúrate de tener el entorno virtual activado:
```powershell
.\.venv\Scripts\Activate.ps1
```

2. Instala las dependencias:
```powershell
pip install -r requirements.txt
```

## ▶️ Ejecutar la aplicación

```powershell
python app.py
```

La aplicación estará disponible en: `http://127.0.0.1:5000`

## 👥 Usuarios de Prueba

### Administrador
- **Email:** admin@rossmix.com
- **Contraseña:** admin123

### Cliente
Puedes registrar un nuevo cliente desde la página de registro.

## 📋 Funcionalidades Implementadas (Fase 1)

✅ Sistema de registro de clientes
✅ Inicio de sesión para clientes y administradores
✅ Panel de administración
✅ Panel de cliente
✅ Base de datos SQLite
✅ Validación de formularios
✅ Mensajes flash informativos
✅ Diseño responsive y moderno

## 🔜 Próximas Funcionalidades

Las siguientes características se implementarán en fases posteriores:

- 📅 Sistema completo de agendamiento de citas
- 🕐 Selección de fecha y hora
- 💅 Selección de servicios (uñas, cabello, depilación, cejas y pestañas)
- 👤 Selección de empleado o aleatorio
- 💰 Sistema de abonos y pagos
- ❌ Cancelación de citas con restricción de tiempo
- 👥 Gestión de empleados por parte del administrador
- 📊 Calendario y historial de citas
- 📧 Notificaciones por email

## 📁 Estructura del Proyecto

```
mi_proyecto_flask/
├── app.py                  # Aplicación principal
├── requirements.txt        # Dependencias
├── rossmix.db             # Base de datos (se crea automáticamente)
└── templates/             # Plantillas HTML
    ├── base.html
    ├── index.html
    ├── login.html
    ├── registro.html
    ├── dashboard_admin.html
    └── dashboard_cliente.html
```

## 🗃️ Estructura de la Base de Datos

### Tabla: Usuario
- id (Integer, Primary Key)
- nombre (String)
- email (String, único)
- telefono (String)
- password (String, hasheada)
- tipo_usuario (String: 'admin' o 'cliente')
- fecha_registro (DateTime)
- activo (Boolean)

## 🔒 Seguridad

- Las contraseñas se almacenan hasheadas usando Werkzeug
- Validación de formularios en el servidor
- Sesiones seguras con Flask
- Mínimo 6 caracteres para contraseñas

## 💡 Notas

- El usuario administrador se crea automáticamente al iniciar la aplicación por primera vez
- La base de datos SQLite se crea automáticamente en el primer inicio
- En producción, cambiar la SECRET_KEY en app.py por una clave segura

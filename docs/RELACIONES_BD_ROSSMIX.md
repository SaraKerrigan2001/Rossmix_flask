# 🗄️ Relaciones de Base de Datos - Rossmix

## 📊 Diagrama de Relaciones

```
┌─────────────────┐
│    USUARIO      │
│─────────────────│
│ • id (PK)       │
│ • nombre        │
│ • email         │
│ • telefono      │
│ • password      │
│ • tipo_usuario  │
│ • activo        │
└─────────────────┘


┌─────────────────┐         ┌──────────────────┐
│    CLIENTES     │◄───────┐│      CITAS       │
│─────────────────│        ││──────────────────│
│ • id_cliente(PK)│        ││ • id_cita (PK)   │
│ • nombre        │        │├─ id_cliente (FK)│◄─┐
│ • celular       │        │├─ id_empleado(FK)│  │
│ • correo        │        │├─ id_servicio(FK)│  │
│ • creado_en     │        ││ • fecha_hora     │  │
└─────────────────┘        ││ • estado         │  │
                           ││ • notas          │  │
                           │└──────────────────┘  │
                           │         ▲            │
                           │         │            │
                           │         │            │
┌─────────────────┐        │         │            │
│   EMPLEADOS     │◄───────┘         │            │
│─────────────────│                  │            │
│ • id_empleado(PK)│◄──┐              │            │
│ • nombre        │   │              │            │
│ • especialidad  │   │              │            │
│ • correo        │   │              │            │
│ • celular       │   │              │            │
└─────────────────┘   │              │            │
      ▲              │              │            │
      │              │              │            │
      │              │              │            │
      │        ┌─────┴──────────┐   │            │
      │        │ EMPLEADO_      │   │            │
      ├────────┤ SERVICIOS      │   │            │
      │        ├────────────────│   │            │
      │        ├─ id_empleado(FK)  │            │
      │        ├─ id_servicio(FK)  │            │
      │        └────────────────┘   │            │
      │              │              │            │
      │              ▼              │            │
┌─────┴──────────┐  ┌───────────────┐           │
│ HORARIOS_      │  │   SERVICIOS   │◄──────────┘
│ EMPLEADOS      │  ├───────────────│
├────────────────│  │ • id_servicio │
│ • id_horario(PK)  │   (PK)        │
├─ id_empleado(FK)  │ • nombre      │
│ • dia_semana   │  │ • descripcion │
│ • hora_inicio  │  │ • duracion    │
│ • hora_fin     │  │ • precio      │
└────────────────┘  └───────────────┘
                           ▲
                           │
                           │
                    ┌──────┴───────┐
                    │    PAGOS     │
                    ├──────────────│
                    │ • id_pago(PK)│
                    ├─ id_cita (FK)│
                    │ • monto      │
                    │ • metodo_pago│
                    │ • fecha_pago │
                    └──────────────┘
```

## 🔗 Relaciones Configuradas

### 1. **EMPLEADO_SERVICIOS** (Tabla Intermedia Many-to-Many)
- `id_empleado` → `empleados.id_empleado`
  - **ON DELETE**: CASCADE (si se elimina el empleado, se eliminan sus asignaciones)
  - **ON UPDATE**: CASCADE
- `id_servicio` → `servicios.id_servicio`
  - **ON DELETE**: CASCADE (si se elimina el servicio, se eliminan las asignaciones)
  - **ON UPDATE**: CASCADE

### 2. **HORARIOS_EMPLEADOS**
- `id_empleado` → `empleados.id_empleado`
  - **ON DELETE**: CASCADE (si se elimina el empleado, se eliminan sus horarios)
  - **ON UPDATE**: CASCADE

### 3. **CITAS**
- `id_cliente` → `clientes.id_cliente`
  - **ON DELETE**: CASCADE (si se elimina el cliente, se eliminan sus citas)
  - **ON UPDATE**: CASCADE

- `id_empleado` → `empleados.id_empleado`
  - **ON DELETE**: SET NULL (si se elimina el empleado, la cita queda sin empleado asignado)
  - **ON UPDATE**: CASCADE

- `id_servicio` → `servicios.id_servicio`
  - **ON DELETE**: RESTRICT (NO permite eliminar servicio si tiene citas)
  - **ON UPDATE**: CASCADE

### 4. **PAGOS**
- `id_cita` → `citas.id_cita`
  - **ON DELETE**: CASCADE (si se elimina la cita, se eliminan sus pagos)
  - **ON UPDATE**: CASCADE

## 📋 Índices Creados

### Tabla CITAS
- `idx_citas_cliente` - Búsqueda por cliente
- `idx_citas_empleado` - Búsqueda por empleado
- `idx_citas_servicio` - Búsqueda por servicio
- `idx_citas_fecha` - Búsqueda por fecha
- `idx_citas_estado` - Búsqueda por estado

### Tabla EMPLEADO_SERVICIOS
- `idx_empleado_servicios_empleado` - Búsqueda por empleado
- `idx_empleado_servicios_servicio` - Búsqueda por servicio

### Tabla HORARIOS_EMPLEADOS
- `idx_horarios_empleado` - Búsqueda por empleado
- `idx_horarios_dia` - Búsqueda por día de la semana

### Tabla PAGOS
- `idx_pagos_cita` - Búsqueda por cita

### Tabla USUARIO
- `idx_usuario_email` - Búsqueda por email (login)
- `idx_usuario_tipo` - Búsqueda por tipo de usuario

### Tabla CLIENTES
- `idx_clientes_correo` - Búsqueda por correo

### Tabla EMPLEADOS
- `idx_empleados_correo` - Búsqueda por correo

## ✔️ Validaciones (Constraints Check)

### HORARIOS_EMPLEADOS
- ✅ `check_dia_semana`: día_semana debe estar entre 0 y 6
- ✅ `check_horario_valido`: hora_fin debe ser mayor que hora_inicio

### SERVICIOS
- ✅ `check_duracion_positiva`: duracion_minutos debe ser > 0
- ✅ `check_precio_positivo`: precio debe ser > 0

### PAGOS
- ✅ `check_monto_positivo`: monto debe ser > 0

## 📝 Notas Importantes

### Estados de Cita (ENUM)
```sql
tipo: estado_cita_enum
valores: 
  - pendiente_pago
  - confirmada
  - en_atencion
  - completada
  - cancelada
  - no_asistio
```

### Días de la Semana (horarios_empleados.dia_semana)
```
0 = Domingo
1 = Lunes
2 = Martes
3 = Miércoles
4 = Jueves
5 = Viernes
6 = Sábado
```

### Tipos de Usuario
```
- admin: Administrador del sistema
- cliente: Cliente que agenda citas
```

## 🔐 Integridad Referencial

La base de datos ahora mantiene **integridad referencial completa**:

1. ✅ No se pueden crear citas con clientes, empleados o servicios inexistentes
2. ✅ No se pueden crear horarios de empleados inexistentes
3. ✅ No se pueden asignar servicios a empleados inexistentes
4. ✅ Si se elimina un cliente, todas sus citas se eliminan automáticamente
5. ✅ Si se elimina un empleado, sus horarios y asignaciones de servicio se eliminan automáticamente
6. ✅ Si se elimina un empleado, sus citas quedan sin empleado asignado (SET NULL)
7. ✅ NO se puede eliminar un servicio que tenga citas asociadas (RESTRICT)
8. ✅ Los pagos se eliminan automáticamente si se elimina la cita

## 🎯 Beneficios

1. **Consistencia de Datos**: Las relaciones garantizan que no haya datos huérfanos
2. **Rendimiento Mejorado**: Los índices aceleran las consultas
3. **Validación Automática**: Los constraints previenen datos inválidos
4. **Mantenimiento Simplificado**: Las acciones CASCADE automatizan la limpieza de datos
5. **Seguridad**: RESTRICT previene eliminaciones accidentales de datos críticos

## 📄 Archivos Relacionados

- `actualizar_relaciones_db.sql` - Script SQL completo para ejecutar en pgAdmin
- `sincronizar_relaciones_final.py` - Script Python para aplicar relaciones
- `verificar_estructura_db.py` - Script para verificar estructura de tablas
- `app.py` - Modelos de SQLAlchemy actualizados

## 🚀 Cómo Aplicar

```bash
# Opción 1: Con Python
python sincronizar_relaciones_final.py

# Opción 2: Con pgAdmin/psql
psql -U postgres -d Rossmix -f actualizar_relaciones_db.sql
```

---

✨ **Base de datos optimizada y con relaciones completas** ✨

# 🐘 Configuración de PostgreSQL para Rossmix

## ✅ Configuración Completada

La aplicación Rossmix ahora está conectada a PostgreSQL en lugar de SQLite.

### 📊 Detalles de la Conexión

- **Base de datos:** rossmix_db
- **Usuario:** postgres
- **Contraseña:** 1234
- **Host:** localhost
- **Puerto:** 5432

### 🗃️ Tablas Creadas

La aplicación creó automáticamente la tabla:

**usuario**
- id (Integer, Primary Key)
- nombre (String)
- email (String, único)
- telefono (String)
- password (String, hasheada)
- tipo_usuario (String: 'admin' o 'cliente')
- fecha_registro (DateTime)
- activo (Boolean)

### 👤 Usuario Administrador

Se creó automáticamente:
- **Email:** admin@rossmix.com
- **Contraseña:** admin123

### 🔧 Comandos Útiles

#### Ver tablas en PostgreSQL:
```sql
-- Conectarse a la base de datos
psql -U postgres -d rossmix_db

-- Listar tablas
\dt

-- Ver estructura de la tabla usuario
\d usuario

-- Ver todos los usuarios
SELECT * FROM usuario;

-- Salir
\q
```

#### Backup de la base de datos:
```bash
pg_dump -U postgres -d rossmix_db > backup_rossmix.sql
```

#### Restaurar backup:
```bash
psql -U postgres -d rossmix_db < backup_rossmix.sql
```

### 📝 Notas Importantes

1. **Migración de datos:** Si tenías datos en SQLite (`rossmix.db`), esos datos NO se migraron automáticamente. El archivo SQLite antiguo sigue existiendo pero ya no se usa.

2. **Ventajas de PostgreSQL:**
   - Mejor rendimiento para múltiples usuarios
   - Más robusto y escalable
   - Mejor para producción
   - Soporte para características avanzadas

3. **Cambiar contraseña:** Para mayor seguridad en producción, cambia la contraseña de PostgreSQL.

4. **String de conexión:** Está en `app.py`:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/rossmix_db'
   ```

### 🚀 Próximos Pasos

La aplicación está lista para continuar el desarrollo con PostgreSQL. Todas las funcionalidades futuras (citas, empleados, servicios, pagos) se guardarán en PostgreSQL.

### ❓ Solución de Problemas

**Si no conecta:**
1. Verifica que PostgreSQL esté ejecutándose
2. Verifica usuario y contraseña
3. Verifica que la base de datos `rossmix_db` exista
4. Ejecuta: `python crear_bd_postgres.py` para verificar la conexión

**Error de permisos:**
```sql
-- Ejecutar en psql como superusuario
GRANT ALL PRIVILEGES ON DATABASE rossmix_db TO postgres;
```

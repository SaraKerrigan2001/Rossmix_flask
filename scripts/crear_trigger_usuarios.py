"""
Script para crear la tabla de auditoría y el trigger en PostgreSQL.
Ejecutar una sola vez: python scripts/crear_trigger_usuarios.py
"""
import sys, os

# Apuntar directamente a app.py (no al paquete app/)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "app_module",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py")
)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app
db  = app_module.db

SQL_AUDITORIA = """
CREATE TABLE IF NOT EXISTS auditoria_usuarios (
    id             SERIAL PRIMARY KEY,
    id_usuario     INTEGER NOT NULL,
    nombre         VARCHAR(100),
    email          VARCHAR(120),
    telefono       VARCHAR(20),
    tipo_usuario   VARCHAR(20),
    fecha_registro TIMESTAMP DEFAULT NOW(),
    accion         VARCHAR(10) DEFAULT 'INSERT'
);
"""

SQL_FUNCION = """
CREATE OR REPLACE FUNCTION fn_auditoria_nuevo_usuario()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO auditoria_usuarios (
        id_usuario, nombre, email, telefono, tipo_usuario, fecha_registro, accion
    ) VALUES (
        NEW.id, NEW.nombre, NEW.email, NEW.telefono,
        NEW.tipo_usuario, NEW.fecha_registro, 'INSERT'
    );

    PERFORM pg_notify(
        'nuevo_usuario',
        json_build_object(
            'id',           NEW.id,
            'nombre',       NEW.nombre,
            'email',        NEW.email,
            'tipo_usuario', NEW.tipo_usuario,
            'fecha',        to_char(NEW.fecha_registro, 'DD/MM/YYYY HH24:MI:SS')
        )::text
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

SQL_TRIGGER = """
DROP TRIGGER IF EXISTS trg_auditoria_nuevo_usuario ON usuario;
CREATE TRIGGER trg_auditoria_nuevo_usuario
    AFTER INSERT ON usuario
    FOR EACH ROW
    EXECUTE FUNCTION fn_auditoria_nuevo_usuario();
"""

SQL_VISTA = """
CREATE OR REPLACE VIEW vista_nuevos_usuarios AS
    SELECT id, id_usuario, nombre, email, telefono,
           tipo_usuario, fecha_registro, accion
    FROM auditoria_usuarios
    ORDER BY fecha_registro DESC;
"""

SQL_VERIFICAR = """
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'trg_auditoria_nuevo_usuario';
"""

def main():
    with app.app_context():
        print("Creando tabla auditoria_usuarios...")
        db.session.execute(db.text(SQL_AUDITORIA))
        db.session.commit()
        print("  OK")

        print("Creando función fn_auditoria_nuevo_usuario...")
        db.session.execute(db.text(SQL_FUNCION))
        db.session.commit()
        print("  OK")

        print("Creando trigger trg_auditoria_nuevo_usuario...")
        db.session.execute(db.text(SQL_TRIGGER))
        db.session.commit()
        print("  OK")

        print("Creando vista vista_nuevos_usuarios...")
        db.session.execute(db.text(SQL_VISTA))
        db.session.commit()
        print("  OK")

        print("\nVerificando trigger en PostgreSQL...")
        rows = db.session.execute(db.text(SQL_VERIFICAR)).fetchall()
        if rows:
            for r in rows:
                print(f"  Trigger:  {r[0]}")
                print(f"  Evento:   {r[1]}")
                print(f"  Tabla:    {r[2]}")
            print("\nTodo listo. Cada nuevo registro quedará en auditoria_usuarios.")
            print("Para verificar en pgAdmin:")
            print("  SELECT * FROM vista_nuevos_usuarios;")
        else:
            print("  ADVERTENCIA: No se encontró el trigger. Revisa los logs.")

if __name__ == "__main__":
    main()

-- ============================================================
-- Migración: agregar columna foto_perfil a la tabla usuario
-- Ejecutar en pgAdmin sobre la BD Rossmix
-- ============================================================

ALTER TABLE usuario
    ADD COLUMN IF NOT EXISTS foto_perfil VARCHAR(200) DEFAULT NULL;

COMMENT ON COLUMN usuario.foto_perfil
    IS 'Ruta relativa a static/uploads/perfiles/ — NULL usa avatar con inicial';

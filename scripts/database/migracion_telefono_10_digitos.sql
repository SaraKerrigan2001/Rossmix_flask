-- Ejecutar sobre una base Rossmix existente.
BEGIN;

DROP VIEW IF EXISTS vista_agenda_diaria CASCADE;
DROP VIEW IF EXISTS vista_pagos_pendientes CASCADE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM usuario
        WHERE telefono !~ '^[0-9]{10}$'
    ) THEN
        RAISE EXCEPTION 'Existen teléfonos que no tienen exactamente 10 dígitos';
    END IF;
END $$;

ALTER TABLE usuario
    ALTER COLUMN telefono TYPE VARCHAR(10);

ALTER TABLE usuario
    DROP CONSTRAINT IF EXISTS ck_usuario_telefono_10_digitos;

ALTER TABLE usuario
    ADD CONSTRAINT ck_usuario_telefono_10_digitos
    CHECK (telefono ~ '^[0-9]{10}$');

CREATE VIEW vista_agenda_diaria AS
SELECT
    c.id_cita,
    c.codigo_reserva,
    u.nombre AS cliente,
    u.telefono,
    u.email,
    e.nombre AS profesional,
    s.nombre_servicio,
    s.duracion_minutos,
    c.fecha_hora_inicio,
    c.fecha_hora_fin,
    TO_CHAR(c.fecha_hora_inicio, 'YYYY-MM-DD') AS fecha_cita,
    TO_CHAR(c.fecha_hora_inicio, 'HH12:MI AM') AS hora_inicio_formato,
    c.monto_total,
    c.monto_abono,
    c.saldo_pendiente,
    c.estado::TEXT AS estado,
    c.reembolsado,
    p.id_pago IS NOT NULL AS pago_registrado,
    p.metodo_pago::TEXT AS metodo_pago,
    p.estado_pago
FROM citas c
JOIN usuario u ON c.id_cliente = u.id
LEFT JOIN empleados e ON c.id_empleado = e.id_empleado
JOIN servicios s ON c.id_servicio = s.id_servicio
LEFT JOIN pagos p ON p.id_cita = c.id_cita;

CREATE VIEW vista_pagos_pendientes AS
SELECT
    c.id_cita,
    c.codigo_reserva,
    u.nombre AS cliente,
    u.telefono,
    s.nombre_servicio,
    c.fecha_hora_inicio,
    c.monto_total,
    c.monto_abono,
    c.saldo_pendiente,
    c.estado::TEXT AS estado
FROM citas c
JOIN usuario u ON c.id_cliente = u.id
JOIN servicios s ON c.id_servicio = s.id_servicio
WHERE c.estado IN ('confirmada', 'en_atencion')
  AND NOT EXISTS (
      SELECT 1 FROM pagos p WHERE p.id_cita = c.id_cita
  )
ORDER BY c.fecha_hora_inicio;

COMMIT;
-- ============================================================================
-- ROSSMIX - BASE DE DATOS DEFINITIVA Y UNIFICADA
-- Versión final: usuario+clientes unificados, pagos conectados a citas
-- Ejecutar en pgAdmin sobre la base de datos "Rossmix"
-- ============================================================================

-- ============================================================================
-- 1. LIMPIEZA COMPLETA (orden inverso por dependencias)
-- ============================================================================
DROP VIEW  IF EXISTS vista_agenda_diaria    CASCADE;
DROP VIEW  IF EXISTS vista_pagos_pendientes CASCADE;
DROP TABLE IF EXISTS auditoria_usuarios     CASCADE;
DROP TABLE IF EXISTS notificaciones         CASCADE;
DROP TABLE IF EXISTS pagos                  CASCADE;
DROP TABLE IF EXISTS citas                  CASCADE;
DROP TABLE IF EXISTS horarios_empleados     CASCADE;
DROP TABLE IF EXISTS empleado_servicios     CASCADE;
DROP TABLE IF EXISTS empleados              CASCADE;
DROP TABLE IF EXISTS servicios              CASCADE;
DROP TABLE IF EXISTS usuario                CASCADE;
DROP TABLE IF EXISTS configuraciones        CASCADE;
DROP TYPE  IF EXISTS estado_cita_enum       CASCADE;
DROP TYPE  IF EXISTS metodo_pago_enum       CASCADE;

-- ============================================================================
-- 2. TIPOS ENUMERADOS
-- ============================================================================
CREATE TYPE estado_cita_enum AS ENUM (
    'pendiente_pago',
    'confirmada',
    'en_atencion',
    'completada',
    'cancelada',
    'no_asistio'
);

CREATE TYPE metodo_pago_enum AS ENUM (
    'efectivo',
    'tarjeta',
    'transferencia',
    'nequi',
    'daviplata'
);

-- ============================================================================
-- 3. TABLA: USUARIO
--    Une clientes + administradores en una sola tabla
--    Campos clientes: celular, correo  |  Campos sistema: email, password
-- ============================================================================
CREATE TABLE usuario (
    id              SERIAL          PRIMARY KEY,
    nombre          VARCHAR(100)    NOT NULL,
    email           VARCHAR(150)    UNIQUE NOT NULL,
    telefono        VARCHAR(20)     NOT NULL,
    password        VARCHAR(200)    NOT NULL,
    tipo_usuario    VARCHAR(20)     NOT NULL DEFAULT 'cliente'
                                    CHECK (tipo_usuario IN ('admin','cliente','especialista')),
    fecha_registro  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    activo          BOOLEAN         DEFAULT TRUE,
    id_empleado     INTEGER         -- FK se agrega después de crear empleados
);

COMMENT ON TABLE  usuario               IS 'Usuarios del sistema: clientes, administradores y especialistas';
COMMENT ON COLUMN usuario.tipo_usuario  IS 'admin = administrador | cliente = cliente final | especialista = empleada con acceso';
COMMENT ON COLUMN usuario.telefono      IS 'Celular/WhatsApp de contacto';
COMMENT ON COLUMN usuario.id_empleado   IS 'Vínculo con empleados para cuentas tipo especialista';

-- ============================================================================
-- 4. TABLA: SERVICIOS
-- ============================================================================
CREATE TABLE servicios (
    id_servicio       SERIAL          PRIMARY KEY,
    nombre_servicio   VARCHAR(100)    NOT NULL,
    descripcion       TEXT,
    precio_total      NUMERIC(10,2)   NOT NULL CHECK (precio_total > 0),
    duracion_minutos  INTEGER         NOT NULL CHECK (duracion_minutos > 0),
    activo            BOOLEAN         DEFAULT TRUE
);

COMMENT ON TABLE servicios IS 'Catálogo de servicios del salón Rossmix';

-- ============================================================================
-- 5. TABLA: EMPLEADOS
-- ============================================================================
CREATE TABLE empleados (
    id_empleado     SERIAL          PRIMARY KEY,
    nombre          VARCHAR(100)    NOT NULL,
    especialidad    VARCHAR(100),
    activo          BOOLEAN         DEFAULT TRUE,
    fecha_registro  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE empleados IS 'Personal especialista del salón';

-- FK diferida: usuario.id_empleado → empleados (se agrega aquí porque usuario se crea antes)
ALTER TABLE usuario
    ADD CONSTRAINT fk_usuario_empleado
        FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado)
        ON DELETE SET NULL ON UPDATE CASCADE;

-- ============================================================================
-- 6. TABLA: EMPLEADO_SERVICIOS (many-to-many)
-- ============================================================================
CREATE TABLE empleado_servicios (
    id_empleado  INTEGER  NOT NULL,
    id_servicio  INTEGER  NOT NULL,
    PRIMARY KEY (id_empleado, id_servicio),
    CONSTRAINT fk_es_empleado
        FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_es_servicio
        FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
        ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE empleado_servicios IS 'Qué servicios puede realizar cada empleado';

-- ============================================================================
-- 7. TABLA: HORARIOS_EMPLEADOS
--    dia_semana: 0=Domingo, 1=Lunes, ..., 6=Sábado
-- ============================================================================
CREATE TABLE horarios_empleados (
    id_horario   SERIAL   PRIMARY KEY,
    id_empleado  INTEGER  NOT NULL,
    dia_semana   INTEGER  NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_inicio  TIME     NOT NULL,
    hora_fin     TIME     NOT NULL,
    CONSTRAINT chk_horario CHECK (hora_fin > hora_inicio),
    CONSTRAINT fk_horario_empleado
        FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado)
        ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON COLUMN horarios_empleados.dia_semana IS '0=Dom 1=Lun 2=Mar 3=Mié 4=Jue 5=Vie 6=Sáb';

-- ============================================================================
-- 8. TABLA: CITAS
--    id_cliente → usuario(id)  [CASCADE: si se borra usuario, se borran sus citas]
--    id_empleado → empleados   [SET NULL: si se borra empleado, cita queda sin asignar]
--    id_servicio → servicios   [RESTRICT: no se puede borrar servicio con citas]
-- ============================================================================
CREATE TABLE citas (
    id_cita           SERIAL          PRIMARY KEY,
    id_cliente        INTEGER         NOT NULL,
    id_empleado       INTEGER,
    id_servicio       INTEGER         NOT NULL,
    fecha_hora_inicio TIMESTAMP       NOT NULL,
    fecha_hora_fin    TIMESTAMP       NOT NULL,
    monto_total       NUMERIC(10,2)   CHECK (monto_total >= 0),
    monto_abono       NUMERIC(10,2)   DEFAULT 5000 CHECK (monto_abono >= 0),
    saldo_pendiente   NUMERIC(10,2),
    estado            estado_cita_enum DEFAULT 'pendiente_pago',
    reembolsado       BOOLEAN         DEFAULT FALSE,
    codigo_reserva    VARCHAR(20)     UNIQUE,       -- ID del ReservaService (RES-XXXXXX)
    token_gestion     VARCHAR(32)     UNIQUE,       -- Token seguro para link de gestión/reprogramación
    notas             TEXT,
    fecha_creacion    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_fechas_cita CHECK (fecha_hora_fin > fecha_hora_inicio),
    CONSTRAINT fk_cita_cliente
        FOREIGN KEY (id_cliente)   REFERENCES usuario(id)
        ON DELETE CASCADE  ON UPDATE CASCADE,
    CONSTRAINT fk_cita_empleado
        FOREIGN KEY (id_empleado)  REFERENCES empleados(id_empleado)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_cita_servicio
        FOREIGN KEY (id_servicio)  REFERENCES servicios(id_servicio)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

COMMENT ON TABLE  citas                  IS 'Reservas agendadas por los clientes';
COMMENT ON COLUMN citas.monto_abono      IS 'Abono mínimo para reservar ($5.000 COP)';
COMMENT ON COLUMN citas.saldo_pendiente  IS 'Se calcula: monto_total - monto_abono';
COMMENT ON COLUMN citas.codigo_reserva   IS 'ID generado por ReservaService (RES-XXXXXX)';
COMMENT ON COLUMN citas.token_gestion    IS 'Token URL-safe para link de gestión/reprogramación';

-- ============================================================================
-- 9. TABLA: PAGOS
--    id_cita → citas [CASCADE: si se borra cita, se borra su pago]
--    Una cita solo puede tener UN pago (UNIQUE en id_cita)
-- ============================================================================
CREATE TABLE pagos (
    id_pago        SERIAL            PRIMARY KEY,
    id_cita        INTEGER           NOT NULL UNIQUE,
    monto          NUMERIC(10,2)     NOT NULL CHECK (monto > 0),
    metodo_pago    metodo_pago_enum  NOT NULL DEFAULT 'efectivo',
    estado_pago    VARCHAR(20)       NOT NULL DEFAULT 'completado'
                                     CHECK (estado_pago IN ('pendiente','completado','reembolsado')),
    referencia     VARCHAR(100),
    fecha_pago     TIMESTAMP         DEFAULT CURRENT_TIMESTAMP,
    notas          TEXT,
    CONSTRAINT fk_pago_cita
        FOREIGN KEY (id_cita) REFERENCES citas(id_cita)
        ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE  pagos             IS 'Pagos registrados por cada cita';
COMMENT ON COLUMN pagos.referencia  IS 'Número de transacción o comprobante';
COMMENT ON COLUMN pagos.metodo_pago IS 'efectivo | tarjeta | transferencia | nequi | daviplata';

-- ============================================================================
-- 10. ÍNDICES PARA RENDIMIENTO
-- ============================================================================
-- Usuario
CREATE INDEX idx_usuario_email      ON usuario(email);
CREATE INDEX idx_usuario_tipo       ON usuario(tipo_usuario);
CREATE INDEX idx_usuario_activo     ON usuario(activo);

-- Servicios / Empleados
CREATE INDEX idx_servicios_activo   ON servicios(activo);
CREATE INDEX idx_empleados_activo   ON empleados(activo);

-- Empleado_servicios
CREATE INDEX idx_es_empleado        ON empleado_servicios(id_empleado);
CREATE INDEX idx_es_servicio        ON empleado_servicios(id_servicio);

-- Horarios
CREATE INDEX idx_horarios_empleado  ON horarios_empleados(id_empleado);
CREATE INDEX idx_horarios_dia       ON horarios_empleados(dia_semana);

-- Citas (las más consultadas)
CREATE INDEX idx_citas_cliente      ON citas(id_cliente);
CREATE INDEX idx_citas_empleado     ON citas(id_empleado);
CREATE INDEX idx_citas_servicio     ON citas(id_servicio);
CREATE INDEX idx_citas_fecha        ON citas(fecha_hora_inicio);
CREATE INDEX idx_citas_estado       ON citas(estado);
CREATE INDEX idx_citas_codigo       ON citas(codigo_reserva);
CREATE INDEX idx_citas_token        ON citas(token_gestion);  -- Para búsqueda por token de gestión

-- Pagos
CREATE INDEX idx_pagos_cita         ON pagos(id_cita);
CREATE INDEX idx_pagos_fecha        ON pagos(fecha_pago);
CREATE INDEX idx_pagos_estado       ON pagos(estado_pago);

-- ============================================================================
-- 11. TABLA: NOTIFICACIONES
--    Alertas internas para usuarios (clientes y admin)
-- ============================================================================
CREATE TABLE notificaciones (
    id          SERIAL          PRIMARY KEY,
    id_usuario  INTEGER         NOT NULL,
    titulo      VARCHAR(200)    NOT NULL,
    mensaje     TEXT,
    target      VARCHAR(300),               -- URL de destino al hacer clic
    leido       BOOLEAN         DEFAULT FALSE,
    fecha       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notif_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE  notificaciones         IS 'Notificaciones internas para clientes y admins';
COMMENT ON COLUMN notificaciones.target  IS 'Ruta Flask a la que redirige la notificación';

CREATE INDEX idx_notif_usuario ON notificaciones(id_usuario);
CREATE INDEX idx_notif_leido   ON notificaciones(leido);
CREATE INDEX idx_notif_fecha   ON notificaciones(fecha);

-- ============================================================================
-- 12. TABLA: AUDITORIA_USUARIOS
--    Registra cada acción relevante sobre cuentas de usuario
--    (creación, edición, desactivación, login, etc.)
--    id_usuario → usuario(id)  [SET NULL: si se borra el usuario, el log se conserva]
--    id_cita    → citas(id_cita) [SET NULL: referencia opcional a una cita relacionada]
-- ============================================================================
CREATE TABLE auditoria_usuarios (
    id              SERIAL          PRIMARY KEY,
    id_usuario      INTEGER,                        -- usuario que fue afectado
    id_actor        INTEGER,                        -- usuario que realizó la acción (admin)
    nombre          VARCHAR(100),                   -- snapshot del nombre al momento de la acción
    email           VARCHAR(120),                   -- snapshot del email
    telefono        VARCHAR(20),                    -- snapshot del teléfono
    tipo_usuario    VARCHAR(20),                    -- snapshot del rol
    accion          VARCHAR(50)     NOT NULL,       -- 'crear','editar','desactivar','login','logout', etc.
    detalle         TEXT,                           -- descripción libre del cambio
    ip_address      VARCHAR(45),                    -- IPv4 o IPv6
    fecha           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_auditoria_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT fk_auditoria_actor
        FOREIGN KEY (id_actor) REFERENCES usuario(id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

COMMENT ON TABLE  auditoria_usuarios          IS 'Registro de auditoría de acciones sobre cuentas de usuario';
COMMENT ON COLUMN auditoria_usuarios.id_usuario  IS 'Usuario afectado por la acción';
COMMENT ON COLUMN auditoria_usuarios.id_actor    IS 'Usuario que ejecutó la acción (ej: admin que editó)';
COMMENT ON COLUMN auditoria_usuarios.accion      IS 'Tipo de acción: crear | editar | desactivar | login | logout | reset_password';
COMMENT ON COLUMN auditoria_usuarios.detalle     IS 'Descripción del cambio, ej: "cambió email de X a Y"';
COMMENT ON COLUMN auditoria_usuarios.ip_address  IS 'Dirección IP desde donde se realizó la acción';

-- Índices para consultas frecuentes de auditoría
CREATE INDEX idx_audit_usuario  ON auditoria_usuarios(id_usuario);
CREATE INDEX idx_audit_actor    ON auditoria_usuarios(id_actor);
CREATE INDEX idx_audit_accion   ON auditoria_usuarios(accion);
CREATE INDEX idx_audit_fecha    ON auditoria_usuarios(fecha);

-- ============================================================================
-- 13. VISTAS
-- ============================================================================

-- Vista agenda diaria completa
CREATE VIEW vista_agenda_diaria AS
SELECT
    c.id_cita,
    c.codigo_reserva,
    u.nombre                                        AS cliente,
    u.telefono,
    u.email,
    e.nombre                                        AS profesional,
    s.nombre_servicio,
    s.duracion_minutos,
    c.fecha_hora_inicio,
    c.fecha_hora_fin,
    TO_CHAR(c.fecha_hora_inicio, 'YYYY-MM-DD')      AS fecha_cita,
    TO_CHAR(c.fecha_hora_inicio, 'HH12:MI AM')      AS hora_inicio_formato,
    c.monto_total,
    c.monto_abono,
    c.saldo_pendiente,
    c.estado::TEXT                                  AS estado,
    c.reembolsado,
    p.id_pago                                       IS NOT NULL AS pago_registrado,
    p.metodo_pago::TEXT                             AS metodo_pago,
    p.estado_pago
FROM citas c
JOIN usuario    u ON c.id_cliente  = u.id
LEFT JOIN empleados  e ON c.id_empleado = e.id_empleado
JOIN servicios  s ON c.id_servicio = s.id_servicio
LEFT JOIN pagos p ON p.id_cita     = c.id_cita;

-- Vista pagos pendientes (citas confirmadas sin pago registrado)
CREATE VIEW vista_pagos_pendientes AS
SELECT
    c.id_cita,
    c.codigo_reserva,
    u.nombre        AS cliente,
    u.telefono,
    s.nombre_servicio,
    c.fecha_hora_inicio,
    c.monto_total,
    c.monto_abono,
    c.saldo_pendiente,
    c.estado::TEXT
FROM citas c
JOIN usuario   u ON c.id_cliente  = u.id
JOIN servicios s ON c.id_servicio = s.id_servicio
WHERE c.estado IN ('confirmada', 'en_atencion')
  AND NOT EXISTS (
      SELECT 1 FROM pagos p WHERE p.id_cita = c.id_cita
  )
ORDER BY c.fecha_hora_inicio;

-- ============================================================================
-- 14. DATOS INICIALES: SERVICIOS
-- ============================================================================
INSERT INTO servicios (nombre_servicio, descripcion, precio_total, duracion_minutos) VALUES
-- Uñas
('Manicure Clásico',         'Limado, esmaltado y cuidado básico de uñas',            25000,  45),
('Manicure con Gel',         'Manicure con esmalte en gel de larga duración',          45000,  60),
('Pedicure Spa',             'Pedicure completo con exfoliación y masaje',             35000,  60),
('Uñas Acrílicas',           'Aplicación de uñas acrílicas con diseño',               80000, 120),
('Decoración de Uñas',       'Diseños artísticos en uñas',                            15000,  30),
-- Cabello
('Corte Dama',               'Corte profesional con lavado y secado',                 30000,  45),
('Corte Caballero',          'Corte masculino con acabados',                          20000,  30),
('Tinte Completo',           'Coloración completa con retoque de raíces',             70000, 120),
('Mechas Balayage',          'Iluminación natural con técnica balayage',             120000, 180),
('Keratina y Alisado',       'Tratamiento de keratina para alisar y nutrir',         150000, 150),
('Brushing y Peinado',       'Secado profesional con plancha o rizos',                25000,  45),
-- Depilación
('Depilación Piernas',       'Depilación con cera piernas completas',                 40000,  45),
('Depilación Axilas',        'Depilación con cera axilas',                            15000,  15),
('Depilación Facial',        'Depilación de bozo y mejillas',                         20000,  30),
-- Cejas y Pestañas
('Diseño de Cejas',          'Perfilado y diseño profesional',                        18000,  30),
('Laminado de Cejas',        'Tratamiento para cejas definidas y voluminosas',        50000,  60),
('Extensiones de Pestañas',  'Aplicación de extensiones pelo a pelo',                 90000,  90),
('Lifting de Pestañas',      'Rizado y definición de pestañas naturales',             55000,  60);

-- ============================================================================
-- 15. DATOS INICIALES: EMPLEADOS
-- ============================================================================
INSERT INTO empleados (nombre, especialidad) VALUES
('María González',   'Especialista en Uñas'),
('Ana Rodríguez',    'Manicurista Profesional'),
('Laura Martínez',   'Nail Artist'),
('Sofía López',      'Estilista Senior'),
('Carolina Pérez',   'Colorista Experta'),
('Valentina Torres', 'Estilista y Maquilladora'),
('Daniela Ramírez',  'Depilación y Estética'),
('Camila Flores',    'Especialista en Cejas'),
('Isabella Castro',  'Extensionista de Pestañas'),
('Gabriela Morales', 'Estilista Integral');

-- ============================================================================
-- 16. DATOS INICIALES: EMPLEADO_SERVICIOS
-- ============================================================================
-- Uñas: María(1), Ana(2), Laura(3)
INSERT INTO empleado_servicios VALUES
(1,1),(1,2),(1,3),(1,4),(1,5),
(2,1),(2,2),(2,3),(2,4),(2,5),
(3,1),(3,2),(3,3),(3,4),(3,5);

-- Cabello: Sofía(4), Carolina(5), Valentina(6)
INSERT INTO empleado_servicios VALUES
(4,6),(4,7),(4,8),(4,9),(4,10),(4,11),
(5,6),(5,7),(5,8),(5,9),(5,10),(5,11),
(6,6),(6,7),(6,8),(6,9),(6,10),(6,11);

-- Depilación: Daniela(7)
INSERT INTO empleado_servicios VALUES
(7,12),(7,13),(7,14);

-- Cejas/Pestañas: Camila(8), Isabella(9)
INSERT INTO empleado_servicios VALUES
(8,15),(8,16),
(9,17),(9,18);

-- Integral: Gabriela(10) — todos los servicios
INSERT INTO empleado_servicios VALUES
(10,1),(10,2),(10,3),(10,4),(10,5),
(10,6),(10,7),(10,8),(10,9),(10,10),(10,11),
(10,12),(10,13),(10,14),(10,15),(10,16),(10,17),(10,18);

-- ============================================================================
-- 17. DATOS INICIALES: HORARIOS (Lun-Vie 8:00-18:00 | Sáb 9:00-16:00)
-- ============================================================================
INSERT INTO horarios_empleados (id_empleado, dia_semana, hora_inicio, hora_fin)
SELECT id_empleado, dia, '08:00', '18:00'
FROM empleados, (VALUES (1),(2),(3),(4),(5)) AS d(dia);

INSERT INTO horarios_empleados (id_empleado, dia_semana, hora_inicio, hora_fin)
SELECT id_empleado, 6, '09:00', '16:00'
FROM empleados;

-- ============================================================================
-- 18. TABLA: CONFIGURACIONES
--    Parámetros configurables del sistema (clave-valor)
--    creado_por → usuario(id)  [SET NULL: si se borra el usuario, la config se conserva]
-- ============================================================================
CREATE TABLE configuraciones (
    id                   SERIAL          PRIMARY KEY,
    clave                VARCHAR(120)    UNIQUE NOT NULL,
    valor                TEXT            NOT NULL,
    descripcion          TEXT,
    creado_por           INTEGER,                        -- FK → usuario que creó el parámetro
    modificado_por       INTEGER,                        -- FK → usuario que lo modificó por última vez
    fecha_creacion       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_config_creado_por
        FOREIGN KEY (creado_por)    REFERENCES usuario(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT fk_config_modificado_por
        FOREIGN KEY (modificado_por) REFERENCES usuario(id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

COMMENT ON TABLE  configuraciones                IS 'Parámetros configurables del sistema (clave-valor)';
COMMENT ON COLUMN configuraciones.clave          IS 'Identificador único del parámetro, ej: abono_minimo';
COMMENT ON COLUMN configuraciones.valor          IS 'Valor del parámetro en texto plano';
COMMENT ON COLUMN configuraciones.creado_por     IS 'ID del usuario admin que creó el parámetro';
COMMENT ON COLUMN configuraciones.modificado_por IS 'ID del usuario admin que modificó el parámetro por última vez';

CREATE INDEX idx_config_clave        ON configuraciones(clave);
CREATE INDEX idx_config_creado_por   ON configuraciones(creado_por);
CREATE INDEX idx_config_modificado   ON configuraciones(modificado_por);

-- Datos iniciales de configuración (creado_por y modificado_por quedan NULL hasta que un admin los gestione)
INSERT INTO configuraciones (clave, valor, descripcion) VALUES
('abono_minimo',        '5000',                      'Monto mínimo de abono para reservar una cita (COP)'),
('anticipacion_minima', '2',                          'Horas mínimas de anticipación para cancelar/reprogramar'),
('max_dias_agenda',     '90',                         'Máximo de días en el futuro que se puede agendar'),
('nombre_salon',        'Rossmix Salón de Belleza',   'Nombre del salón que aparece en emails y PDFs'),
('moneda',              'COP',                        'Moneda utilizada en precios');

-- ============================================================================
-- 19. VERIFICACIÓN FINAL
-- ============================================================================
SELECT 'usuario'             AS tabla, COUNT(*) AS registros FROM usuario          UNION ALL
SELECT 'servicios',                    COUNT(*) FROM servicios                     UNION ALL
SELECT 'empleados',                    COUNT(*) FROM empleados                     UNION ALL
SELECT 'empleado_servicios',           COUNT(*) FROM empleado_servicios            UNION ALL
SELECT 'horarios_empleados',           COUNT(*) FROM horarios_empleados            UNION ALL
SELECT 'citas',                        COUNT(*) FROM citas                         UNION ALL
SELECT 'pagos',                        COUNT(*) FROM pagos                         UNION ALL
SELECT 'notificaciones',               COUNT(*) FROM notificaciones                UNION ALL
SELECT 'auditoria_usuarios',           COUNT(*) FROM auditoria_usuarios            UNION ALL
SELECT 'configuraciones',              COUNT(*) FROM configuraciones;

-- ============================================================================
-- CONSULTAS ÚTILES EN PGADMIN:
--
--   Ver agenda de hoy:
--     SELECT * FROM vista_agenda_diaria
--     WHERE fecha_cita = CURRENT_DATE ORDER BY hora_inicio_formato;
--
--   Ver citas con saldo pendiente:
--     SELECT * FROM vista_pagos_pendientes;
-- ============================================================================

-- ============================================================
-- SISTEMA RESTAURANTE - SCHEMA DEFINITIVO (MER v4)
-- PostgreSQL
-- ============================================================

-- Extensión para IDs universales (concurrencia/offline)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- CONFIGURACIÓN GLOBAL DEL LOCAL
-- ============================================================
CREATE TABLE configuracion (
    clave        VARCHAR(50) PRIMARY KEY,
    valor        TEXT NOT NULL,
    descripcion  TEXT
);

-- Valores por defecto (el admin puede cambiarlos en el panel)
INSERT INTO configuracion (clave, valor, descripcion) VALUES
('nombre_local',        'PUNTO FIJO BURGERS',       'Nombre del restaurante que sale en el recibo'),
('iva_porcentaje',      '19',                       'IVA en porcentaje, incluido en el precio final'),
('minutos_cocina',      '28',                       'Temporizador por defecto de cocina (minutos)'),
('modo_impuestos',      'INCLUIDO',                 'INCLUIDO = el precio ya lleva IVA y se separa en recibo'),
('max_rondas_disponible','1',                       'Futuro: rondas'),
('didi_comision_pct',   '0',                        'Comisión DiDi (solo referencia informativa)'),
('politica_stock_insuficiente', 'BLOQUEAR',         'Política ante faltante de stock: BLOQUEAR o ADVERTIR_Y_PERMITIR');

-- ============================================================
-- ROLES Y USUARIOS
-- ============================================================
CREATE TABLE rol (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(30) NOT NULL UNIQUE,   -- admin | cajero | mesero | cocina
    descripcion TEXT
);

INSERT INTO rol (nombre, descripcion) VALUES
('admin',   'Acceso total: ventas, ganancias, inventario, recetas, gastos, cancelaciones'),
('cajero',  'Cobrar, vales, pedidos Didi, cierre de su turno, devoluciones de dinero'),
('mesero',  'Tomar y enviar pedidos, ver mesas, preparados y estado de cocina. Sin dinero'),
('cocina',  'Ver tickets (sin precios), cambiar estados, temporizador');

CREATE TABLE usuario (
    id               SERIAL PRIMARY KEY,
    rol_id           INT NOT NULL REFERENCES rol(id),
    nombre           VARCHAR(100) NOT NULL,
    usuario          VARCHAR(50) NOT NULL UNIQUE,
    password_hash    TEXT NOT NULL,             -- hash (passlib/bcrypt)
    activo           BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- CATÁLOGO DE PRODUCTOS
-- ============================================================
CREATE TABLE tipo_categoria (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(20) NOT NULL UNIQUE         -- COMIDA | BEBIDA | OTRO
);
INSERT INTO tipo_categoria (nombre) VALUES ('COMIDA'), ('BEBIDA'), ('OTRO');

CREATE TABLE categoria (
    id          SERIAL PRIMARY KEY,
    tipo_id     INT NOT NULL REFERENCES tipo_categoria(id),
    nombre      VARCHAR(50) NOT NULL,
    orden       INT NOT NULL DEFAULT 0,
    activo      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE producto (
    id                 SERIAL PRIMARY KEY,
    categoria_id       INT NOT NULL REFERENCES categoria(id),
    nombre             VARCHAR(100) NOT NULL,
    descripcion        TEXT,
    imagen_url         TEXT,
    precio             NUMERIC(12,2) NOT NULL DEFAULT 0,   -- PRECIO FINAL al cliente (IVA incluido)
    iva_incluido       BOOLEAN NOT NULL DEFAULT TRUE,
    manual_disponible  BOOLEAN,                 -- NULL = automático por stock; TRUE/FALSE = forzado por admin
    activo             BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en          TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- INGREDIENTES, CATEGORÍAS DE INSUMOS Y RECETAS
-- ============================================================
CREATE TABLE proveedor (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    contacto    VARCHAR(100),
    telefono    VARCHAR(30),
    activo      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE categoria_insumo (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    activo      BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO categoria_insumo (id, nombre, descripcion) VALUES
(1, 'CARNES', 'Carnes de res, pollo, salchichas, tocineta'),
(2, 'VERDURAS', 'Tomate, lechuga, cebolla, etc.'),
(3, 'PANADERIA', 'Panes para hamburguesa y perro'),
(4, 'LACTEOS', 'Queso cheddar, mozzarella, costeño'),
(5, 'SALSAS_CONDIMENTOS', 'Salsas de la casa, mayonesa, ketchup, chimichurri'),
(6, 'ABARROTES_ACEITES', 'Papa cruda, aceites, harinas, sal'),
(7, 'BEBIDAS', 'Gaseosas, aguas, pulpas, cervezas'),
(8, 'DESECHABLES_EMPAQUES', 'Servilletas, vasos, cajas, bolsas'),
(9, 'OTRO', 'Otros insumos no categorizados')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE ingrediente (
    id                  SERIAL PRIMARY KEY,
    categoria_insumo_id INT REFERENCES categoria_insumo(id),
    nombre              VARCHAR(100) NOT NULL,
    unidad_base         VARCHAR(20) NOT NULL CHECK (unidad_base IN ('GRAMO','MILILITRO','UNIDAD','LONJA','PORCION','PAQUETE')),
    costo_unitario      NUMERIC(12,4) NOT NULL DEFAULT 0,   -- costo por unidad base (cómo llegó)
    costo_proveedor     TEXT,                              -- descripción libre: "kg de carne $14.000" (informativo)
    stock_actual        NUMERIC(12,4) NOT NULL DEFAULT 0,   -- proyección rápida; sum(movimientos) es la fuente
    stock_minimo        NUMERIC(12,4) NOT NULL DEFAULT 0,
    stock_ideal         NUMERIC(12,4),
    proveedor_id        INT REFERENCES proveedor(id),
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE detalle_receta (
    id            SERIAL PRIMARY KEY,
    product_id    INT NOT NULL REFERENCES producto(id) ON DELETE CASCADE,
    ingrediente_id INT NOT NULL REFERENCES ingrediente(id),
    cantidad      NUMERIC(12,4) NOT NULL,        -- admite fracciones: 0.75 tomate, 2 lonjas, 250 g
    unidad        VARCHAR(20) NOT NULL,          -- unidad con la que se expresa en la receta (u, lonja, g, ml)
    UNIQUE (product_id, ingrediente_id)
);

CREATE TABLE componente_combo (
    id                 SERIAL PRIMARY KEY,
    combo_producto_id  INT NOT NULL REFERENCES producto(id) ON DELETE CASCADE,
    producto_hijo_id   INT NOT NULL REFERENCES producto(id) ON DELETE CASCADE,
    cantidad           NUMERIC(10,2) NOT NULL DEFAULT 1,
    UNIQUE (combo_producto_id, producto_hijo_id)
);

-- ============================================================
-- MESAS
-- ============================================================
CREATE TABLE mesa (
    id         SERIAL PRIMARY KEY,
    numero     INT NOT NULL UNIQUE,
    estado     VARCHAR(20) NOT NULL DEFAULT 'DISPONIBLE' CHECK (estado IN ('DISPONIBLE','EN_CURSO','OCUPADA')),
    activo     BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO mesa (numero) VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9);

-- ============================================================
-- PEDIDOS
-- ============================================================
CREATE TABLE pedido (
    id            SERIAL PRIMARY KEY,
    consecutivo   INT NOT NULL,                   -- numeración por día (ticket visible)
    fecha_dia     DATE NOT NULL DEFAULT CURRENT_DATE,  -- para reiniciar consecutivo por día
    canal         VARCHAR(20) NOT NULL CHECK (canal IN ('MESA','MOSTRADOR','DIDI','DOMICILIO')),
    mesa_id       INT REFERENCES mesa(id),        -- solo para canal MESA
    usuario_id    INT NOT NULL REFERENCES usuario(id),  -- mesero/registrador
    estado        VARCHAR(25) NOT NULL DEFAULT 'NUEVO'
                  CHECK (estado IN ('NUEVO','ENVIADO_A_COCINA','EN_PREPARACION','FINALIZADO','ENTREGADO','PAGADO','CERRADO','CANCELADO')),
    -- Datos de domicilio / didi
    cliente       VARCHAR(100),
    telefono      VARCHAR(30),
    direccion     TEXT,
    nota_interna  TEXT,                           -- nota que ve cocina ("sin tomate", "USAR PREPARADO")
    didi_orden_id VARCHAR(50),                    -- número de orden de la app DiDi
    -- Totales (se gravan al cobrar; se recalculan si cambian)
    subtotal      NUMERIC(12,2) NOT NULL DEFAULT 0,
    iva           NUMERIC(12,2) NOT NULL DEFAULT 0,
    total         NUMERIC(12,2) NOT NULL DEFAULT 0,
    motivo_cancelacion TEXT,                      -- obligatorio si estado = CANCELADO
    idempotency_key VARCHAR(100) UNIQUE,          -- clave de idempotencia para evitar duplicados offline
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    enviado_en       TIMESTAMPTZ,
    finalizado_en    TIMESTAMPTZ,
    pagado_en        TIMESTAMPTZ,
    cancelado_en     TIMESTAMPTZ,

    -- Umbral de producción para regla de cancelación:
    -- una línea cuenta como "producida" si su copia_detalle pasó a PREPARANDO/LISTO/ENTREGADO
    UNIQUE (fecha_dia, consecutivo)
);

CREATE INDEX IF NOT EXISTS ix_pedido_idempotency_key ON pedido(idempotency_key);

CREATE INDEX idx_pedido_mesa  ON pedido (mesa_id) WHERE canal = 'MESA';
CREATE INDEX idx_pedido_estado ON pedido (estado);
CREATE INDEX idx_pedido_fecha ON pedido (fecha_dia, consecutivo);

-- ============================================================
-- DETALLE PEDIDO (líneas / rondas)
-- ============================================================
CREATE TABLE detalle_pedido (
    id                  SERIAL PRIMARY KEY,
    pedido_id           INT NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    ronda               INT NOT NULL DEFAULT 1,        -- ronda 1, 2, 3... (cada ronda va a cocina aparte)
    producto_id         INT NOT NULL REFERENCES producto(id),
    cantidad            NUMERIC(10,2) NOT NULL DEFAULT 1,
    precio_unitario     NUMERIC(12,2) NOT NULL,         -- precio capturado al momento (congelado)
    variacion_snapshot  JSONB,                          -- modificaciones: {"doble_carne":true,"sin_tomate":true,"extra":[...]}
    estado              VARCHAR(20) NOT NULL DEFAULT 'ENVIADO'
                        CHECK (estado IN ('ENVIADO','PREPARANDO','LISTO','ENTREGADO','CANCELADO')),
    preparado_en        TIMESTAMPTZ,                    -- cuando cocina ACEPTA -> momento de descuento de insumos
    listo_en            TIMESTAMPTZ,
    entregado_en        TIMESTAMPTZ,
    cancelado_en        TIMESTAMPTZ
);

CREATE INDEX idx_detalle_pedido ON detalle_pedido (pedido_id);
CREATE INDEX idx_detalle_estado ON detalle_pedido (estado);

-- ============================================================
-- PAGOS
-- ============================================================
CREATE TABLE pago (
    id             SERIAL PRIMARY KEY,
    pedido_id      INT NOT NULL REFERENCES pedido(id),
    cierre_id      INT,                                -- FK a cierre (se completa al cerrar turno)
    metodo         VARCHAR(20) NOT NULL
                   CHECK (metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA','VALE','DIDI_TARJETA','DIDI_EFECTIVO')),
    monto          NUMERIC(12,2) NOT NULL,
    recibido       NUMERIC(12,2),                       -- SOLO efectivo (para calcular cambio)
    cambio         NUMERIC(12,2),
    didi_orden_id  VARCHAR(50),                         -- para los métodos DIDI
    estado         VARCHAR(15) NOT NULL DEFAULT 'VALIDO' CHECK (estado IN ('VALIDO','DEVUELTO')),
    usuario_id     INT REFERENCES usuario(id),          -- cajero que cobra
    devuelto_por   INT REFERENCES usuario(id),
    devuelto_en    TIMESTAMPTZ,
    motivo_devolucion TEXT,
    pagado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- VALE (PAGARÉ) — venta a crédito de personas de confianza
-- ============================================================
CREATE TABLE vale (
    id                SERIAL PRIMARY KEY,
    pedido_id         INT NOT NULL REFERENCES pedido(id),
    cliente_nombre    VARCHAR(100) NOT NULL,
    cliente_cedula    VARCHAR(20),
    cliente_telefono  VARCHAR(30),
    monto             NUMERIC(12,2) NOT NULL,
    estado            VARCHAR(15) NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE','COBRADO')),
    cobrado_por       INT REFERENCES usuario(id),
    cobrado_en        TIMESTAMPTZ,
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- MOVIMIENTOS DE DINERO (caja) — SOLO ADMIN (egresos/entradas con descripción obligatoria)
-- ============================================================
CREATE TABLE movimiento_caja (
    id           SERIAL PRIMARY KEY,
    usuario_id   INT NOT NULL REFERENCES usuario(id),    -- administrador
    tipo         VARCHAR(10) NOT NULL CHECK (tipo IN ('ENTRADA','SALIDA')),
    categoria    VARCHAR(20) NOT NULL
                 CHECK (categoria IN ('PAGO_TURNO','PRESTAMO','ADELANTO','PROVEEDOR','DEVOLUCION','COBRO_VALE','CAMBIO_INICIAL','OTRO')),
    concepto     VARCHAR(100) NOT NULL,
    descripcion  TEXT NOT NULL,                          -- OBLIGATORIA (regla del dueño)
    valor        NUMERIC(12,2) NOT NULL,                 -- SIEMPRE positivo; el signo lo da tipo
    pedido_id    INT REFERENCES pedido(id),              -- cuando es devolución de pedido
    vale_id      INT REFERENCES vale(id),                -- cuando es cobro de vale
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- La columna cierre_id y su FK se agregan al final (después de crear la tabla cierre).

-- ============================================================
-- INVENTARIO — MOVIMIENTOS (la fuente de verdad / historial)
-- ============================================================
CREATE TABLE movimiento_inventario (
    id                     SERIAL PRIMARY KEY,
    ingrediente_id         INT NOT NULL REFERENCES ingrediente(id),
    pedido_id              INT REFERENCES pedido(id),        -- referencia cuando es consumo por venta
    compra_id              INT,                              -- se agrega FK abajo (compra se define después)
    usuario_id             INT NOT NULL REFERENCES usuario(id),
    cantidad               NUMERIC(12,4) NOT NULL,           -- NEGATIVO = salida (venta) ; POSITIVO = entrada (compra)
    unidad                 VARCHAR(20) DEFAULT 'u',
    saldo_anterior         NUMERIC(12,4),
    saldo_nuevo            NUMERIC(12,4),
    costo_unitario_momento NUMERIC(12,4),
    tipo                   VARCHAR(20) NOT NULL
                           CHECK (tipo IN ('VENTA','COMPRA','MERMA','AJUSTE','DEVOLUCION','DESPERDICIO')),
    referencia             TEXT,                             -- texto libre "Pedido #152"
    creado_en              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- CIERRE DE TURNO (fotograma inmutable)
-- ============================================================
CREATE TABLE cierre (
    id                 SERIAL PRIMARY KEY,
    usuario_id         INT NOT NULL REFERENCES usuario(id),   -- cajero que cierra
    abierto_en         TIMESTAMPTZ NOT NULL,                                -- apertura del turno (NULLS cerrado_en = turno ABIERTO todavía)
    cerrado_en         TIMESTAMPTZ,                                          -- se llena al cerrar el turno (fotograma)
    total_pedidos      INT NOT NULL DEFAULT 0,
    total_venta_comida NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_venta_bebida NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_efectivo     NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_tarjeta      NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_transferencia NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_vale         NUMERIC(12,2) NOT NULL DEFAULT 0,
    cantidad_vales     INT NOT NULL DEFAULT 0,
    total_didi_tarjeta NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_didi_efectivo NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_entradas_caja NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_salidas_caja  NUMERIC(12,2) NOT NULL DEFAULT 0,
    cantidad_egresos    INT NOT NULL DEFAULT 0,
    total_devoluciones  NUMERIC(12,2) NOT NULL DEFAULT 0,
    preparados_reutilizados INT NOT NULL DEFAULT 0,
    preparados_descartados  INT NOT NULL DEFAULT 0,
    total_ventas       NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_efectivo_final NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_por_cobrar   NUMERIC(12,2) NOT NULL DEFAULT 0,      -- DiDi tarjeta + vales pendientes
    notas              TEXT
);

-- Un solo turno abierto a la vez (índice parcial único)
CREATE UNIQUE INDEX uq_cierre_unico_abierto ON cierre ((cerrado_en IS NULL)) WHERE cerrado_en IS NULL;

-- Conexión pago -> cierre
ALTER TABLE pago ADD CONSTRAINT fk_pago_cierre FOREIGN KEY (cierre_id) REFERENCES cierre(id);
ALTER TABLE movimiento_caja ADD COLUMN cierre_id INT;
ALTER TABLE movimiento_caja ADD CONSTRAINT fk_movcaja_cierre FOREIGN KEY (cierre_id) REFERENCES cierre(id);

-- ============================================================
-- PREPARADOS (producto producido de pedido cancelado, reutilizable)
-- ============================================================
CREATE TABLE preparado (
    id                SERIAL PRIMARY KEY,
    producto_id       INT NOT NULL REFERENCES producto(id),
    pedido_origen_id  INT NOT NULL REFERENCES pedido(id),
    detalle_origen_id INT NOT NULL REFERENCES detalle_pedido(id),
    variacion_snapshot JSONB,
    cantidad          NUMERIC(10,2) NOT NULL DEFAULT 1,
    estado            VARCHAR(15) NOT NULL DEFAULT 'DISPONIBLE' CHECK (estado IN ('DISPONIBLE','ASIGNADO','DESCARTADO')),
    pedido_nuevo_id   INT REFERENCES pedido(id),         -- pedido que lo reutilizó
    usuario_id        INT REFERENCES usuario(id),        -- quien asignó/descartó
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
    asignado_en       TIMESTAMPTZ,
    descartado_en     TIMESTAMPTZ,
    motivo_descarte   TEXT
);

-- ============================================================
-- COMPRAS Y PROVEEDORES
-- ============================================================
CREATE TABLE compra (
    id           SERIAL PRIMARY KEY,
    proveedor_id INT REFERENCES proveedor(id),
    usuario_id   INT NOT NULL REFERENCES usuario(id),   -- admin
    descripcion  TEXT,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE detalle_compra (
    id             SERIAL PRIMARY KEY,
    compra_id      INT NOT NULL REFERENCES compra(id) ON DELETE CASCADE,
    ingrediente_id INT NOT NULL REFERENCES ingrediente(id),
    cantidad       NUMERIC(12,4) NOT NULL,     -- en unidad base del ingrediente
    costo_unitario NUMERIC(12,4) NOT NULL,     -- costo al que llegó (por unidad base)
    costo_total    NUMERIC(12,4) NOT NULL
);

-- FK de movimiento_inventario hacia compra (definida al final)
ALTER TABLE movimiento_inventario ADD CONSTRAINT fk_movinv_compra FOREIGN KEY (compra_id) REFERENCES compra(id);

-- ============================================================
-- AUDITORÍA (historial de acciones - nada se borra)
-- ============================================================
CREATE TABLE historial_accion (
    id          SERIAL PRIMARY KEY,
    usuario_id  INT REFERENCES usuario(id),
    accion      VARCHAR(100) NOT NULL,       -- CREAR_PEDIDO, CANCELAR_PEDIDO, AJUSTAR_INVENTARIO, MODIFICAR_PRECIO, EGRESO, ...
    entidad     VARCHAR(50),                 -- pedido, producto, ingrediente, pago, vale...
    entidad_id  INT,
    detalle     TEXT,
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_historial_fecha ON historial_accion (creado_en);
CREATE INDEX idx_historial_usuario ON historial_accion (usuario_id);

-- ============================================================
-- SEED DE CATEGORÍAS Y PRODUCTOS DE EJEMPLO (para desarrollo)
-- ============================================================
INSERT INTO categoria (tipo_id, nombre, orden) VALUES
((SELECT id FROM tipo_categoria WHERE nombre='COMIDA'), 'HAMBURGUESAS', 1),
((SELECT id FROM tipo_categoria WHERE nombre='COMIDA'), 'PERROS',        2),
((SELECT id FROM tipo_categoria WHERE nombre='COMIDA'), 'ACOMPAÑAMIENTOS',3),
((SELECT id FROM tipo_categoria WHERE nombre='BEBIDA'), 'BEBIDAS',       4),
((SELECT id FROM tipo_categoria WHERE nombre='BEBIDA'), 'POSTRES',       5);

INSERT INTO producto (categoria_id, nombre, descripcion, precio) VALUES
((SELECT id FROM categoria WHERE nombre='HAMBURGUESAS'), 'Hamburguesa Clásica', 'Pan, carne, queso, lechuga', 12000),
((SELECT id FROM categoria WHERE nombre='HAMBURGUESAS'), 'Hamburguesa Especial', 'Doble carne, queso cheddar, tomate', 15000),
((SELECT id FROM categoria WHERE nombre='PERROS'),        'Perro Clásico',       'Salchicha, pan, salsas', 8000),
((SELECT id FROM categoria WHERE nombre='ACOMPAÑAMIENTOS'),'Papas Fritas',        'Porción de 150 g', 6000),
((SELECT id FROM categoria WHERE nombre='BEBIDAS'),       'Gaseosa',             '350 ml', 3000),
((SELECT id FROM categoria WHERE nombre='BEBIDAS'),       'Agua',               '500 ml', 2000);

-- ============================================================
INSERT INTO proveedor (id, nombre, contacto, telefono) VALUES
(1, 'Distribuidora Central Cali', 'Don Pedro', '3123456789')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ingrediente (nombre, unidad_base, costo_unitario, costo_proveedor, stock_actual, stock_minimo) VALUES
('Pan',            'UNIDAD',   500,    'Pan baguette $500/unidad',      40, 10),
('Carne',          'GRAMO',    56,     'Kg de carne $56.000',          5000, 1500),
('Queso Cheddar',  'LONJA',    800,    'Lonja de cheddar $800',         100, 30),
('Tomate',         'UNIDAD',   2000,   'Tomate $2.000/unidad',           20, 5),
('Lechuga',        'GRAMO',    25,     'Kg de lechuga $25.000',         1500, 400),
('Salsa',          'MILILITRO',2,      'Galón de salsa $8.000',        5000, 1000),
('Salchicha',      'UNIDAD',   1500,   'Paquete x10 $15.000',            60, 20),
('Papas',          'GRAMO',    3,      'Kg de papa $3.000',            8000, 2000),
('Gaseosa',        'UNIDAD',   2000,   'Caja x24 $48.000',               96, 24);

-- Hamburguesa Especial: pan 2 u · carne 125 g · cheddar 2 lonjas · tomate 0.75 u · lechuga 30 g · salsa 20 ml
INSERT INTO detalle_receta (product_id, ingrediente_id, cantidad, unidad)
SELECT p.id, i.id, c.cantidad, c.unidad
FROM producto p
CROSS JOIN (VALUES
    ('Pan', 2,   'u'),
    ('Carne', 125, 'g'),
    ('Queso Cheddar', 2, 'lonja'),
    ('Tomate', 0.75, 'u'),
    ('Lechuga', 30, 'g'),
    ('Salsa', 20, 'ml')
) AS c(nombre_ing, cantidad, unidad)
JOIN ingrediente i ON i.nombre = c.nombre_ing
WHERE p.nombre = 'Hamburguesa Especial';

-- Hamburguesa Clásica: pan 2 u · carne 125 g · queso 1 lonja · lechuga 20 g · salsa 15 ml
INSERT INTO detalle_receta (product_id, ingrediente_id, cantidad, unidad)
SELECT p.id, i.id, c.cantidad, c.unidad
FROM producto p
CROSS JOIN (VALUES
    ('Pan', 2,   'u'),
    ('Carne', 125, 'g'),
    ('Queso Cheddar', 1, 'lonja'),
    ('Lechuga', 20, 'g'),
    ('Salsa', 15, 'ml')
) AS c(nombre_ing, cantidad, unidad)
JOIN ingrediente i ON i.nombre = c.nombre_ing
WHERE p.nombre = 'Hamburguesa Clásica';

-- Perro Clásico: pan 1 u · salchicha 1 u · salsa 15 ml
INSERT INTO detalle_receta (product_id, ingrediente_id, cantidad, unidad)
SELECT p.id, i.id, c.cantidad, c.unidad
FROM producto p
CROSS JOIN (VALUES
    ('Pan', 1, 'u'),
    ('Salchicha', 1, 'u'),
    ('Salsa', 15, 'ml')
) AS c(nombre_ing, cantidad, unidad)
JOIN ingrediente i ON i.nombre = c.nombre_ing
WHERE p.nombre = 'Perro Clásico';

-- ============================================================
-- SEED DE USUARIOS (contraseña temporal: se actualiza en el primer login/por admin)
-- ============================================================
-- Contraseñas demo (solo desarrollo): admin/admin123, caja/caja123, mesero/mesero123, cocina/cocina123
INSERT INTO usuario (rol_id, nombre, usuario, password_hash) VALUES
((SELECT id FROM rol WHERE nombre='admin'),  'Administrador', 'admin',  '$2b$12$/8tbC/F.WtMNVjSvRdwG9ecoLMDXColvgCAqeP2bAVVZcS/STbS.O'),
((SELECT id FROM rol WHERE nombre='cajero'), 'Cajero Demo',    'caja',   '$2b$12$UR9zR9cwj5ffRV9B9oJdteyUkDG5MKTTuANe8aYzqZ1hv0VO70cc.'),
((SELECT id FROM rol WHERE nombre='mesero'), 'Mesero Demo',    'mesero', '$2b$12$ns9jFXxoo26ThkiIjdd7y.C/0POZqvxPRMKW5spYxCB3aIQ3JP5r6'),
((SELECT id FROM rol WHERE nombre='cocina'), 'Cocina Demo',    'cocina', '$2b$12$vMsDVdpD.xW494pwpmb2k.gyxGbDLOvKdRRo2KLUDOErIjy75yiwa');
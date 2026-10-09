-- ============================================================
-- MIGRACIÓN 04 - COLUMNAS ES_DEMO, EMPAQUES, ASISTENCIA Y OPERACIÓN
-- ============================================================

-- 1. Marcas fijado y es_demo en usuario
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS fijado BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Turno laboral: rol y es_demo (REQUERIDO PARA OPERARIOS Y CAJEROS)
ALTER TABLE turno_laboral ADD COLUMN IF NOT EXISTS rol VARCHAR(50) NOT NULL DEFAULT 'cajero';
ALTER TABLE turno_laboral ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_turno_laboral_es_demo ON turno_laboral(es_demo);

-- 3. Columna es_demo en todas las tablas transaccionales
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_pedido_es_demo ON pedido(es_demo);

ALTER TABLE pago ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_pago_es_demo ON pago(es_demo);

ALTER TABLE vale ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_vale_es_demo ON vale(es_demo);

ALTER TABLE movimiento_caja ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_movimiento_caja_es_demo ON movimiento_caja(es_demo);

ALTER TABLE cierre ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_cierre_es_demo ON cierre(es_demo);

ALTER TABLE movimiento_inventario ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_movimiento_inventario_es_demo ON movimiento_inventario(es_demo);

ALTER TABLE compra ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_compra_es_demo ON compra(es_demo);

ALTER TABLE historial_accion ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_historial_accion_es_demo ON historial_accion(es_demo);

ALTER TABLE preparado ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_preparado_es_demo ON preparado(es_demo);

-- 4. Columnas operativas en producto y pedido
ALTER TABLE producto ADD COLUMN IF NOT EXISTS empaque_llevar_id INT REFERENCES producto(id);
ALTER TABLE producto ADD COLUMN IF NOT EXISTS permite_adiciones BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE producto ADD COLUMN IF NOT EXISTS manual_disponible BOOLEAN;

ALTER TABLE pedido ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100) UNIQUE;
CREATE INDEX IF NOT EXISTS ix_pedido_idempotency_key ON pedido(idempotency_key);

ALTER TABLE detalle_receta ADD COLUMN IF NOT EXISTS solo_llevar BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS tipo_articulo VARCHAR(30) DEFAULT 'INSUMO_RECETA';
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS precio_venta NUMERIC(12, 2) DEFAULT 0;
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS tipo_consumo VARCHAR(15) DEFAULT 'LOCAL';
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS recargo_empaque NUMERIC(12, 2) DEFAULT 0;

-- 5. Movimiento de caja y cierre
ALTER TABLE movimiento_caja ADD COLUMN IF NOT EXISTS cierre_id INT;
ALTER TABLE movimiento_caja DROP CONSTRAINT IF EXISTS fk_movcaja_cierre;
ALTER TABLE movimiento_caja ADD CONSTRAINT fk_movcaja_cierre FOREIGN KEY (cierre_id) REFERENCES cierre(id);
ALTER TABLE movimiento_caja DROP CONSTRAINT IF EXISTS ck_movcaja_categoria;
ALTER TABLE movimiento_caja ADD CONSTRAINT ck_movcaja_categoria CHECK (categoria IN ('PAGO_TURNO','PRESTAMO','ADELANTO','PROVEEDOR','DEVOLUCION','COBRO_VALE','CAMBIO_INICIAL','GASTO_OPERATIVO','OTRO'));

CREATE INDEX IF NOT EXISTS idx_movcaja_creado_en ON movimiento_caja (creado_en);
CREATE INDEX IF NOT EXISTS idx_movcaja_cierre ON movimiento_caja (cierre_id);

-- 6. Política de stock: permitir ventas continuas sin bloqueo en caja
INSERT INTO configuracion (clave, valor, descripcion)
VALUES ('politica_stock_insuficiente', 'ADVERTIR_Y_PERMITIR', 'Política ante faltante de stock')
ON CONFLICT (clave) DO UPDATE SET valor = 'ADVERTIR_Y_PERMITIR';


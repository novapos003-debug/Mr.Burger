-- ============================================================
-- MR. BURGER — MIGRACIÓN 04: EMPAQUES DINÁMICOS Y GASTOS OPERATIVOS
-- ============================================================

-- 1. Modificar detalle_receta para soportar insumos exclusivos para llevar (C1, P1, Bolsas)
ALTER TABLE detalle_receta ADD COLUMN IF NOT EXISTS solo_llevar BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Modificar ingrediente para soportar tipo_articulo y precio_venta al cliente
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS tipo_articulo VARCHAR(30) DEFAULT 'INSUMO_RECETA';
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS precio_venta NUMERIC(12, 2) DEFAULT 0;

-- 3. Modificar pedido para soportar tipo_consumo y recargo_empaque explícito
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS tipo_consumo VARCHAR(15) DEFAULT 'LOCAL';
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS recargo_empaque NUMERIC(12, 2) DEFAULT 0;

-- 4. Actualizar restricción de movimiento_caja para incluir GASTO_OPERATIVO
ALTER TABLE movimiento_caja DROP CONSTRAINT IF EXISTS ck_movcaja_categoria;
ALTER TABLE movimiento_caja ADD CONSTRAINT ck_movcaja_categoria 
CHECK (categoria IN ('PAGO_TURNO','PRESTAMO','ADELANTO','PROVEEDOR','DEVOLUCION','COBRO_VALE','CAMBIO_INICIAL','GASTO_OPERATIVO','OTRO'));

-- 5. Desactivar productos obsoletos de prueba (1 a 6) y el empaque 999 para que no aparezcan en la carta de comida
UPDATE producto SET activo = FALSE WHERE id IN (1, 2, 3, 4, 5, 6, 999);

-- 6. Desactivar ingredientes iniciales obsoletos sin categoría (1 a 9)
UPDATE ingrediente SET activo = FALSE WHERE id IN (1, 2, 3, 4, 5, 6, 7, 8, 9);

-- 7. Asegurar categoria_insumo 8 (DESECHABLES_EMPAQUES) y 10 (GASTOS_OPERATIVOS)
INSERT INTO categoria_insumo (id, nombre, descripcion) VALUES
(8, 'DESECHABLES_EMPAQUES', 'Contenedores C1, P1, bolsas T20-T40, vasos y servilletas'),
(10, 'GASTOS_OPERATIVOS', 'Artículos de aseo, papelería y mantenimiento')
ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre;

-- 8. Actualizar C1 y P1 con sus precios de venta oficiales para llevar
UPDATE ingrediente 
SET nombre = 'C1 (Empaque Térmico)', 
    tipo_articulo = 'DESECHABLE_SERVICIO',
    costo_unitario = 500.00,
    precio_venta = 1500.00,
    activo = TRUE
WHERE nombre ILIKE '%c1%' OR id = 61;

UPDATE ingrediente 
SET nombre = 'P1 (Porta Perro Caliente)', 
    tipo_articulo = 'DESECHABLE_SERVICIO',
    costo_unitario = 350.00,
    precio_venta = 500.00,
    activo = TRUE
WHERE nombre ILIKE '%porta perro%' OR id = 68;

-- 9. Insertar Bolsas T20, T25, T30, T40 y Papel de cocina
INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, precio_venta, activo)
VALUES 
('Bolsa T20 (Para Llevar Pequeña)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 100.00, 0.00, TRUE),
('Bolsa T25 (Para Llevar Mediana)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 150.00, 0.00, TRUE),
('Bolsa T30 (Para Llevar Grande)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 200.00, 0.00, TRUE),
('Bolsa T40 (Para Llevar Extra Grande)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 300.00, 0.00, TRUE),
('Papel de cocina', 10, 'GASTO_OPERATIVO', 'UNIDAD', 3500.00, 0.00, TRUE)
ON CONFLICT DO NOTHING;

-- 10. Actualizar secuencias
SELECT setval('ingrediente_id_seq', (SELECT MAX(id) FROM ingrediente));

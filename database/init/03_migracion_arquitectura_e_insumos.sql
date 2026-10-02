-- ============================================================
-- MR. BURGER — MIGRACIÓN DE ARQUITECTURA E INSUMOS REALES
-- ============================================================

-- 1. MIGRACIÓN DEL ESQUEMA (Implementación de Gastos vs Insumos)
-- ============================================================

-- A. Añadir Categoría de Gasto Operativo
INSERT INTO categoria_insumo (id, nombre, descripcion) 
VALUES (10, 'GASTOS_OPERATIVOS', 'Artículos de aseo, papelería y mantenimiento (NO RECETAS)')
ON CONFLICT (id) DO UPDATE SET nombre = 'GASTOS_OPERATIVOS';

-- B. Modificar la tabla Ingrediente para soportar el Tipo de Artículo estricto
-- Usaremos una columna ENUM simulada o VARCHAR por compatibilidad
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS tipo_articulo VARCHAR(30) DEFAULT 'INSUMO_RECETA' 
CHECK (tipo_articulo IN ('INSUMO_RECETA', 'VENTA_DIRECTA', 'DESECHABLE_SERVICIO', 'GASTO_OPERATIVO'));

-- C. Modificar la tabla Pedido para soportar Tipo de Consumo
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS tipo_consumo VARCHAR(15) DEFAULT 'LOCAL'
CHECK (tipo_consumo IN ('LOCAL', 'LLEVAR'));

-- C.2 Modificar la tabla Producto para enlazar su empaque dinámico
ALTER TABLE producto ADD COLUMN IF NOT EXISTS empaque_llevar_id INT REFERENCES producto(id) ON DELETE SET NULL;

-- D. Registrar Configuración para el recargo dinámico del Empaque (c1)
INSERT INTO configuracion (clave, valor, descripcion) 
VALUES 
('sku_empaque_llevar', 'c1', 'Código (SKU) del empaque principal a cobrar en pedidos PARA LLEVAR'),
('precio_empaque_llevar', '1500', 'Precio dinámico del empaque (c1) que se cobra al cliente')
ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor;

-- ============================================================
-- 2. SEMILLAS (INSERCIÓN DE INSUMOS REALES)
-- ============================================================

-- Borrar ingredientes de prueba si es necesario (Opcional, pero recomendado para producción)
-- DELETE FROM detalle_receta;
-- DELETE FROM ingrediente;

-- A. CARNES (categoria_insumo_id = 1)
INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, activo) VALUES
('Carne de res', 1, 'INSUMO_RECETA', 'GRAMO', 30.00, true),
('Carne Angus', 1, 'INSUMO_RECETA', 'GRAMO', 50.00, true),
('Pollo (Pechuga)', 1, 'INSUMO_RECETA', 'GRAMO', 25.00, true),
('Baby Beef', 1, 'INSUMO_RECETA', 'GRAMO', 40.00, true),
('Churrasco', 1, 'INSUMO_RECETA', 'GRAMO', 40.00, true),
('Costilla', 1, 'INSUMO_RECETA', 'GRAMO', 35.00, true),
('Tocineta', 1, 'INSUMO_RECETA', 'GRAMO', 20.00, true),
('Salchicha Ideal', 1, 'INSUMO_RECETA', 'UNIDAD', 1200.00, true),
('Salchicha Ranchera', 1, 'INSUMO_RECETA', 'UNIDAD', 1500.00, true),
('Salchicha Suiza', 1, 'INSUMO_RECETA', 'UNIDAD', 1800.00, true),
('Salchicha Americana', 1, 'INSUMO_RECETA', 'UNIDAD', 1400.00, true);

-- B. PANADERIA Y ACOMPAÑANTES (categoria_insumo_id = 3)
INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, activo) VALUES
('Pan Hamburguesa', 3, 'INSUMO_RECETA', 'UNIDAD', 800.00, true),
('Pan Perro', 3, 'INSUMO_RECETA', 'UNIDAD', 700.00, true),
('Pan Brillo', 3, 'INSUMO_RECETA', 'UNIDAD', 900.00, true),
('Papa a la Francesa', 6, 'INSUMO_RECETA', 'GRAMO', 5.00, true),
('Mazorcas', 6, 'INSUMO_RECETA', 'UNIDAD', 2500.00, true),
('Aros de Cebolla', 6, 'INSUMO_RECETA', 'UNIDAD', 400.00, true),
('Ripio de Papa', 6, 'INSUMO_RECETA', 'GRAMO', 8.00, true),
('Arepas', 3, 'INSUMO_RECETA', 'UNIDAD', 600.00, true);

-- C. VEGETALES (categoria_insumo_id = 2)
INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, activo) VALUES
('Tomate', 2, 'INSUMO_RECETA', 'UNIDAD', 500.00, true),
('Cebolla Cabezona', 2, 'INSUMO_RECETA', 'GRAMO', 2.00, true),
('Cebolla Morada', 2, 'INSUMO_RECETA', 'GRAMO', 3.00, true),
('Lechuga Batavia', 2, 'INSUMO_RECETA', 'GRAMO', 4.00, true),
('Lechuga Crespa', 2, 'INSUMO_RECETA', 'GRAMO', 5.00, true),
('Limones', 2, 'INSUMO_RECETA', 'UNIDAD', 300.00, true);

-- D. LACTEOS Y SALSAS (categoria_insumo_id = 4 y 5)
INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, activo) VALUES
('Queso Americano', 4, 'INSUMO_RECETA', 'LONJA', 800.00, true),
('Queso Tajado', 4, 'INSUMO_RECETA', 'LONJA', 600.00, true),
('Queso Vitafilado', 4, 'INSUMO_RECETA', 'GRAMO', 25.00, true),
('Queso Cheddar', 4, 'INSUMO_RECETA', 'LONJA', 900.00, true),
('Leche', 4, 'INSUMO_RECETA', 'MILILITRO', 3.00, true),
('Mantequilla', 4, 'INSUMO_RECETA', 'GRAMO', 15.00, true),
('Chimichurry', 5, 'INSUMO_RECETA', 'MILILITRO', 10.00, true),
('Salsa Mr Burger', 5, 'INSUMO_RECETA', 'MILILITRO', 12.00, true),
('Salsa de Tomate', 5, 'INSUMO_RECETA', 'MILILITRO', 8.00, true),
('Salsa BBQ', 5, 'INSUMO_RECETA', 'MILILITRO', 10.00, true),
('Mayonesa', 5, 'INSUMO_RECETA', 'MILILITRO', 9.00, true),
('Salsa Piña', 5, 'INSUMO_RECETA', 'MILILITRO', 11.00, true),
('Mostaza', 5, 'INSUMO_RECETA', 'MILILITRO', 8.00, true),
('Vinagreta', 5, 'INSUMO_RECETA', 'MILILITRO', 15.00, true),
('Aceite', 6, 'INSUMO_RECETA', 'MILILITRO', 6.00, true);

-- E. BEBIDAS Y PULPAS (categoria_insumo_id = 7)
INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, activo) VALUES
('Cerveza', 7, 'VENTA_DIRECTA', 'UNIDAD', 3500.00, true),
('Gaseosa 400ml', 7, 'VENTA_DIRECTA', 'UNIDAD', 2500.00, true),
('Gaseosa litro 1/4', 7, 'VENTA_DIRECTA', 'UNIDAD', 6000.00, true),
('Agua Botella', 7, 'VENTA_DIRECTA', 'UNIDAD', 2000.00, true),
('Pulpa Maracuyá', 7, 'INSUMO_RECETA', 'UNIDAD', 1200.00, true),
('Pulpa Mango', 7, 'INSUMO_RECETA', 'UNIDAD', 1200.00, true),
('Pulpa Mandarina', 7, 'INSUMO_RECETA', 'UNIDAD', 1200.00, true),
('Pulpa Fresa', 7, 'INSUMO_RECETA', 'UNIDAD', 1200.00, true),
('Pulpa Mora', 7, 'INSUMO_RECETA', 'UNIDAD', 1200.00, true),
('Pulpa Guanábana', 7, 'INSUMO_RECETA', 'UNIDAD', 1500.00, true),
('Limonada de Coco (Insumos Base)', 7, 'INSUMO_RECETA', 'PORCION', 2000.00, true);

-- F. DESECHABLES DE SERVICIO (categoria_insumo_id = 8)
-- Crear categoría ADICIONALES/OTROS si no existe
INSERT INTO categoria (id, tipo_id, nombre, orden, activo) 
VALUES (99, 3, 'OTROS SERVICIOS', 9, TRUE)
ON CONFLICT (id) DO NOTHING;

-- El empaque c1 también se añade acá como producto para que pueda facturarse (invisible en menú de mesero)
INSERT INTO producto (id, categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(999, 99, 'Empaque Para Llevar (c1)', 'Empaque térmico principal desechable', 1500.00, TRUE, TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, activo) VALUES
('Empaque Principal (c1)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 500.00, true),
('Vaso Grande', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 300.00, true),
('Vaso Pequeño', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 200.00, true),
('Vaso 12oz', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 250.00, true),
('Copa y Tapa', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 400.00, true),
('Pitillo', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 20.00, true),
('Servilletas', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 10.00, true),
('Porta Perro', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 350.00, true),
('Bolsa Empaque', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 150.00, true),
('Papel Aluminio', 8, 'DESECHABLE_SERVICIO', 'GRAMO', 5.00, true);

-- G. GASTOS OPERATIVOS NO INSUMOS (categoria_insumo_id = 10)
-- IMPORTANTE: El tipo_articulo es 'GASTO_OPERATIVO', bloqueado para recetas.
INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, activo) VALUES
('Axion (Lavaplatos)', 10, 'GASTO_OPERATIVO', 'UNIDAD', 5500.00, true),
('Jabón en polvo', 10, 'GASTO_OPERATIVO', 'UNIDAD', 4500.00, true),
('Límpido', 10, 'GASTO_OPERATIVO', 'UNIDAD', 3000.00, true),
('Fabuloso', 10, 'GASTO_OPERATIVO', 'UNIDAD', 4000.00, true),
('Esponjas', 10, 'GASTO_OPERATIVO', 'UNIDAD', 1500.00, true),
('Papel de baño', 10, 'GASTO_OPERATIVO', 'UNIDAD', 2500.00, true),
('Rollos impresora térmica', 10, 'GASTO_OPERATIVO', 'UNIDAD', 3500.00, true),
('Guantes de cocina', 10, 'GASTO_OPERATIVO', 'UNIDAD', 12000.00, true),
('Tapabocas', 10, 'GASTO_OPERATIVO', 'UNIDAD', 800.00, true);

-- Ajustar secuencias
SELECT setval('ingrediente_id_seq', (SELECT MAX(id) FROM ingrediente));

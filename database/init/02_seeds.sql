-- ============================================================
-- MR. BURGER — SEMILLAS OFICIALES DEL MENÚ
-- Fuente: Menú físico original (lado1.jpeg y lado2.jpeg)
-- ============================================================

-- 1. Asegurar Tipos de Categoría
INSERT INTO tipo_categoria (id, nombre) VALUES 
(1, 'COMIDA'), 
(2, 'BEBIDA'), 
(3, 'OTRO')
ON CONFLICT (id) DO NOTHING;

-- 2. Categorías Principales del Menú
INSERT INTO categoria (id, tipo_id, nombre, orden, activo) VALUES
(1, 1, 'HAMBURGUESAS', 1, TRUE),
(2, 1, 'COMBOS', 2, TRUE),
(3, 1, 'PERROS CALIENTES', 3, TRUE),
(4, 1, 'ASADOS', 4, TRUE),
(5, 1, 'MAZORCAS Y DESGRANADOS', 5, TRUE),
(6, 1, 'ALITAS', 6, TRUE),
(7, 1, 'PARA COMPARTIR Y ADICIONES', 7, TRUE),
(8, 2, 'BEBIDAS', 8, TRUE)
ON CONFLICT (id) DO UPDATE SET 
    nombre = EXCLUDED.nombre,
    orden = EXCLUDED.orden,
    tipo_id = EXCLUDED.tipo_id;

-- Ajustar la secuencia de categorías para futuras inserciones
SELECT setval('categoria_id_seq', (SELECT MAX(id) FROM categoria));

-- 3. Productos Oficiales de Mr. Burger

-- A. HAMBURGUESAS
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
-- Especial
(1, 'Hamburguesa Especial Res', 'Carne de res, tocineta, queso, tomate, lechuga, ripio y salsas', 18900.00, TRUE, TRUE),
(1, 'Hamburguesa Especial Doble Res', 'Doble carne de res, tocineta, queso, tomate, lechuga, ripio y salsas', 21900.00, TRUE, TRUE),
(1, 'Hamburguesa Especial Pollo', 'Pechuga de pollo, tocineta, queso, tomate, lechuga, ripio y salsas', 21600.00, TRUE, TRUE),
(1, 'Hamburguesa Especial Doble Pollo', 'Doble pechuga de pollo, tocineta, queso, tomate, lechuga, ripio y salsas', 24600.00, TRUE, TRUE),
(1, 'Hamburguesa Especial Mixta', 'Carne de res y pollo, tocineta, queso, tomate, lechuga, ripio y salsas', 25900.00, TRUE, TRUE),
-- Mr. Burger
(1, 'Hamburguesa Mr. Burger Doble Res', 'Todo doble (no vegetales, no ripio): deliciosos aros de cebolla fritos, doble queso americano y más tocineta', 25700.00, TRUE, TRUE),
(1, 'Hamburguesa Mr. Burger Doble Pollo', 'Todo doble con pollo (no vegetales, no ripio): aros de cebolla fritos, doble queso americano y tocineta', 25900.00, TRUE, TRUE),
(1, 'Hamburguesa Mr. Burger Doble Angus', 'Doble carne Angus, aros de cebolla fritos, doble queso americano y tocineta', 35000.00, TRUE, TRUE),
-- Angus
(1, 'Hamburguesa Angus Sencilla', 'Pan artesanal, carne 100% ANGUS, queso americano, más tocineta, cebolla morada y lechuga romana', 31000.00, TRUE, TRUE),
(1, 'Hamburguesa Angus Doble', 'Pan artesanal, doble carne 100% ANGUS, queso americano, más tocineta, cebolla morada y lechuga romana', 35000.00, TRUE, TRUE),
-- Todo Terreno
(1, 'Hamburguesa T.T Todo Terreno Res', 'Carne de res, doble tocineta, extra queso mozarella, cebolla grillé', 22900.00, TRUE, TRUE),
(1, 'Hamburguesa T.T Todo Terreno Doble Res', 'Doble carne de res, doble tocineta, extra queso mozarella, cebolla grillé', 25900.00, TRUE, TRUE),
(1, 'Hamburguesa T.T Todo Terreno Pollo', 'Pollo, doble tocineta, extra queso mozarella, cebolla grillé', 23100.00, TRUE, TRUE),
(1, 'Hamburguesa T.T Todo Terreno Doble Pollo', 'Doble pollo, doble tocineta, extra queso mozarella, cebolla grillé', 25500.00, TRUE, TRUE),
(1, 'Hamburguesa T.T Todo Terreno Mixta', 'Carne y pollo, doble tocineta, extra queso mozarella, cebolla grillé', 27500.00, TRUE, TRUE),
-- Ranchera
(1, 'Hamburguesa Ranchera Res', 'Carne de res, 2 salchichas Rancheras con queso rallado y chimichurri', 22500.00, TRUE, TRUE),
(1, 'Hamburguesa Ranchera Doble Res', 'Doble carne de res, 2 salchichas Rancheras con queso rallado y chimichurri', 25500.00, TRUE, TRUE),
-- Cinco Estrellas
(1, 'Hamburguesa Cinco Estrellas Res', 'Carne de res, aros de cebolla, queso americano, tocineta (no ripio)', 22900.00, TRUE, TRUE),
(1, 'Hamburguesa Cinco Estrellas Doble Res', 'Doble carne de res, aros de cebolla, queso americano, tocineta (no ripio)', 25200.00, TRUE, TRUE);

-- B. COMBOS
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(2, 'Combo Con Papas', 'Gaseosa personal + porción de papas a la francesa', 15000.00, TRUE, TRUE),
(2, 'Combo Con Aros de Cebolla', 'Gaseosa personal + porción de aros de cebolla crocantes', 16500.00, TRUE, TRUE);

-- C. PERROS CALIENTES
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(3, 'Perro Ítalo Suizo', 'Salchicha Suiza, tocineta, queso mozarella, ripio, lechuga y salsa de la casa', 19900.00, TRUE, TRUE),
(3, 'Perro Mr. Burger', 'Salchicha Ideal, tocineta, queso mozarella, ripio, lechuga y salsa de la casa', 16500.00, TRUE, TRUE),
(3, 'Perro Ranchero', 'Dos salchichas Rancheras, tocineta, queso mozarella, ripio, lechuga y salsa de la casa', 17900.00, TRUE, TRUE),
(3, 'Perro Americano', 'Salchicha Americana, tocineta, queso americano y salsa de la casa', 18700.00, TRUE, TRUE),
(3, 'Perro Quesudo', 'Salchicha Americana, tocineta, mucho queso mozzarella, maíz dulce y salsa de la casa', 19700.00, TRUE, TRUE),
(3, 'Perro Mexicano', 'Salchicha Ideal, tocineta, queso rallado, ripio, lechuga, chimichurri y salsa de la casa', 16900.00, TRUE, TRUE);

-- D. ASADOS
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(4, 'Costilla St. Louis', 'Costilla baby de cerdo bañada en salsa BBQ, acompañada de papas a la francesa y ensalada fresca', 36400.00, TRUE, TRUE),
(4, 'Asado Baby', 'Lomo viche a la brasa con chimichurri y BBQ, con papas y ensalada fresca', 35400.00, TRUE, TRUE),
(4, 'Churrasco a la Brasa', 'Churrasco a la brasa con chimichurri y BBQ, con papas y ensalada fresca', 32200.00, TRUE, TRUE),
(4, 'Filete de Pollo a la Brasa', 'Filete de pechuga de pollo con chimichurri y BBQ, con papas y ensalada fresca', 32400.00, TRUE, TRUE),
(4, 'Chuzo de Res', 'Carne de res en pincho a la brasa, con papas y ensalada fresca', 22300.00, TRUE, TRUE),
(4, 'Chuzo de Pollo', 'Pollo en pincho a la brasa, con papas y ensalada fresca', 22300.00, TRUE, TRUE),
(4, 'Chuzo Mixto', 'Carne de res y pollo en pincho a la brasa, con papas y ensalada fresca', 22300.00, TRUE, TRUE);

-- E. MAZORCAS Y DESGRANADOS
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(5, 'Desgranado Mixto', 'Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, lechuga, ripio de papa, res y pollo', 33500.00, TRUE, TRUE),
(5, 'Desgranado Res', 'Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, lechuga, ripio de papa y res', 30500.00, TRUE, TRUE),
(5, 'Desgranado Pollo', 'Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, lechuga, ripio de papa y pollo', 30500.00, TRUE, TRUE),
(5, 'Desgranado Ranchero', 'Mazorca desgranada con mantequilla, salsa de la casa, queso rallado, ripio y salchicha ranchera', 33000.00, TRUE, TRUE),
(5, 'Mazorca Ranchera', 'Mazorca tierna con salchicha ranchera y cubierta de abundante queso rallado', 18500.00, TRUE, TRUE),
(5, 'Mazorca Gratinada', 'Mazorca tierna bañada en salsa de la casa y gratinada con queso mozzarella', 17400.00, TRUE, TRUE),
(5, 'Mazorca Americana', 'Mazorca tierna tradicional con mantequilla y salsa americana', 15900.00, TRUE, TRUE),
(5, 'Mazorca Especial Pollo', 'Mazorca tierna acompañada con trozos de pechuga de pollo y queso rallado', 24500.00, TRUE, TRUE);

-- F. ALITAS
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(6, 'Alitas BBQ (6 piezas)', '6 piezas de alas apanadas bañadas en salsa BBQ, acompañadas con papas a la francesa', 21900.00, TRUE, TRUE),
(6, 'Alitas Miel Mostaza (6 piezas)', '6 piezas de alas apanadas bañadas en salsa miel mostaza, con papas a la francesa', 21900.00, TRUE, TRUE),
(6, 'Alitas Picantes (6 piezas)', '6 piezas de alas apanadas bañadas en salsa picante especial, con papas a la francesa', 21900.00, TRUE, TRUE);

-- G. PARA COMPARTIR & ADICIONES
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(7, 'Salchipapa Americana', 'Papas a la francesa crocantes con salchicha Americana y salsas', 19900.00, TRUE, TRUE),
(7, 'Salchipapa Especial', 'Papas a la francesa con salchicha americana, queso rallado, queso mozzarella y tocineta', 23600.00, TRUE, TRUE),
(7, 'Papas con Queso', 'Porción generosa de papas a la francesa cubiertas con queso fundido y tocineta', 17900.00, TRUE, TRUE),
(7, 'Papas a la Francesa (Porción)', 'Porción individual de papas a la francesa crocantes', 12000.00, TRUE, TRUE),
(7, 'Aros de Cebolla (6 unidades)', '6 aros de cebolla fritos dorados y crocantes', 13000.00, TRUE, TRUE);

-- H. BEBIDAS
INSERT INTO producto (categoria_id, nombre, descripcion, precio, iva_incluido, activo) VALUES
(8, 'Limonada Natural', 'Limonada refrescante preparada al instante', 7700.00, TRUE, TRUE),
(8, 'Limonada de Coco', 'Limonada cremosa con leche de coco y hielo frappé', 9900.00, TRUE, TRUE),
(8, 'Limonada Cherry', 'Limonada refrescante con infusión dulce de cereza', 9900.00, TRUE, TRUE),
(8, 'Jugo de Mandarina', 'Jugo natural de mandarina recién exprimida', 8300.00, TRUE, TRUE),
(8, 'Jugos en Agua', 'Jugo natural de fruta en agua (Mora, Mango, Lulo, Maracuyá)', 8000.00, TRUE, TRUE),
(8, 'Jugos en Leche', 'Jugo natural de fruta en leche fresca', 9000.00, TRUE, TRUE),
(8, 'Gaseosa Personal', 'Gaseosa en presentación personal (Coca-Cola, Postobón, etc.)', 5500.00, TRUE, TRUE),
(8, 'Gaseosa 1.1/4 Litro', 'Gaseosa tamaño familiar 1.1/4 L', 12000.00, TRUE, TRUE),
(8, 'Fuze Tea', 'Té frío embotellado sabor limón / durazno', 5500.00, TRUE, TRUE),
(8, 'Agua en Botella', 'Agua pura sin gas en botella personal', 5000.00, TRUE, TRUE),
(8, 'Cerveza Nacional', 'Cerveza fría personal (Club Colombia, Águila, Poker)', 7000.00, TRUE, TRUE);

-- Ajustar la secuencia de productos para futuras inserciones
SELECT setval('producto_id_seq', (SELECT MAX(id) FROM producto));

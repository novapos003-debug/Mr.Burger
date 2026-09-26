# Estado del Proyecto POS Mr. Burger & Plan de Trabajo para Mañana

**Fecha de guardado:** 21 de Septiembre de 2026  
**Cliente:** Mr. Burger (Cali)  
**Fuente de verdad del proyecto:** [README.md](file:///C:/Users/jhona/Documents/Default%20Project/README.md)

---

## 1. Contexto y Requerimientos Clave del Cliente

1. **Catálogo Real Digitalizado:**
   - Obtenido directamente de las imágenes del menú físico en `figuras/lado1.jpeg` y `figuras/lado2.jpeg`.
2. **Regla de Oro en la Interfaz Móvil del Mesero:**
   - **NO colocar fotos individuales por cada producto en la vista del mesero.**
   - Motivo: Evitar saturación visual, ahorro de espacio en pantallas táctiles de celulares/tablets y agilidad máxima (tomar el pedido en pocos segundos con botones directos y selectores compactos de variantes).
3. **Activos Gráficos Procesados y Listos:**
   - Logo oficial recortado, fondo transparente y sin rebordes:
     - `frontend/public/logo.png`
     - `frontend/public/favicon.png`
     - `frontend/public/assets/images/logo_transparent.png`
     - `frontend/public/assets/images/logo_badge.png`
   - Fotos limpias representativas de comida (para encabezados/categorías):
     - `burger_angus_clean.png`, `burger_especial_clean.png`, `asado_clean.png`, `bebida_clean.png`, `desgranado_clean.png`.

---

## 2. Catálogo Oficial Mr. Burger (Listo para Inserción en BD)

### A. Categoría: HAMBURGUESAS
| Producto | Tipo / Variación | Precio ($ COP) | Descripción del Menú |
| :--- | :--- | :--- | :--- |
| **Especial** | Res | $18.900 | Carne o pollo, tocineta, queso, tomate, lechuga, ripio y salsas |
| | Doble Res | $21.900 | |
| | Pollo | $21.600 | |
| | Doble Pollo | $24.600 | |
| | Mixta | $25.900 | |
| **Mr. Burger** | Doble Res | $25.700 | Todo lo tiene doble (no vegetales, no ripio). Deliciosos aros de cebolla fritos, doble queso americano y más tocineta |
| | Doble Pollo | $25.900 | |
| | Doble Angus | $35.000 | |
| **Angus** | Sencilla | $31.000 | Pan artesanal, carne 100% ANGUS, queso americano, más tocineta, cebolla morada y lechuga romana |
| | Doble | $35.000 | |
| **T.T Todo Terreno** | Res | $22.900 | Carne de res o pollo, doble tocineta, extra queso mozarella, cebolla grillé |
| | Doble Res | $25.900 | |
| | Pollo | $23.100 | |
| | Doble Pollo | $25.500 | |
| | Mixta | $27.500 | |
| **Ranchera** | Res | $22.500 | Carne de res o pollo, 2 salchichas Rancheras con queso rallado y chimichurri |
| | Doble Res | $25.500 | |
| **Cinco Estrellas** | Res | $22.900 | Carne de res o pollo, aros de cebolla, queso americano, tocineta (no ripio) |
| | Doble Res | $25.200 | |

### B. Categoría: COMBOS
| Producto | Detalle | Precio ($ COP) |
| :--- | :--- | :--- |
| **Combo Con Papas** | Gaseosa personal + porción de papas | $15.000 |
| **Combo Con Aros de Cebolla** | Gaseosa personal + aros de cebolla | $16.500 |

### C. Categoría: PERROS CALIENTES
| Producto | Descripción | Precio ($ COP) |
| :--- | :--- | :--- |
| **Ítalo Suizo** | Salchicha Suiza, tocineta, queso mozarella, ripio, lechuga y salsa de la casa | $19.900 |
| **Mr. Burger** | Salchicha Ideal, tocineta, queso mozarella, ripio, lechuga y salsa de la casa | $16.500 |
| **Ranchero** | Dos salchichas Rancheras, tocineta, queso mozarella, ripio, lechuga y salsa de la casa | $17.900 |
| **Americano** | Salchicha Americana, tocineta, queso americano y salsa de la casa | $18.700 |
| **Quesudo** | Salchicha Americana, tocineta, mucho queso mozzarella, maíz dulce y salsa de la casa | $19.700 |
| **Mexicano** | Salchicha Ideal, tocineta, queso rallado, ripio, lechuga, chimichurri y salsa de la casa | $16.900 |

### D. Categoría: ASADOS
*(Todos acompañados de papas a la francesa y ensalada fresca)*
| Producto | Detalle | Precio ($ COP) |
| :--- | :--- | :--- |
| **Costilla St. Louis** | Costilla baby de cerdo bañada en salsa BBQ | $36.400 |
| **Baby** | Lomo viche a la brasa, con chimichurri y BBQ | $35.400 |
| **Churrasco** | Churrasco a la brasa con chimichurri y BBQ | $32.200 |
| **Filete de Pollo** | Filete de pechuga de pollo con chimichurri y BBQ | $32.400 |
| **Chuzo de Res** | Carne de res en pincho a la brasa | $22.300 |
| **Chuzo de Pollo** | Pollo en pincho a la brasa | $22.300 |
| **Chuzo Mixto** | Carne de res y pollo en pincho a la brasa | $22.300 |

### E. Categoría: MAZORCAS Y DESGRANADOS
*(Con mantequilla, salsa de la casa, queso rallado, lechuga, ripio de papa y carne)*
| Producto | Tipo / Variación | Precio ($ COP) |
| :--- | :--- | :--- |
| **Desgranado Mixto** | Mixto | $33.500 |
| **Desgranado Res** | Res | $30.500 |
| **Desgranado Pollo** | Pollo | $30.500 |
| **Desgranado Ranchero** | Ranchero | $33.000 |
| *Opción Dividido* | Extra | +$10.000 |
| **Mazorca Ranchera** | Cubierta de queso rallado | $18.500 |
| **Mazorca Gratinada** | Gratinada | $17.400 |
| **Mazorca Americana** | Americana | $15.900 |
| **Mazorca Especial Pollo** | Especial pollo | $24.500 |

### F. Categoría: ALITAS
| Producto | Detalle | Precio ($ COP) |
| :--- | :--- | :--- |
| **Alitas (6 piezas)** | Apanadas en salsa a elección (BBQ, Miel Mostaza o Picantes), con papas a la francesa | $21.900 |

### G. Categoría: PARA COMPARTIR & ADICIONES
| Producto | Detalle | Precio ($ COP) |
| :--- | :--- | :--- |
| **Salchipapa** | Papas a la francesa con salchicha Americana | $19.900 |
| **Salchipapa Especial** | Queso rallado, queso mozzarella y tocineta | $23.600 |
| **Papas con Queso** | Papas con queso y tocineta | $17.900 |
| **Papas a la Francesa** | Porción individual | $12.000 |
| **Aros de Cebolla** | 6 unidades | $13.000 |

### H. Categoría: BEBIDAS
| Producto | Precio ($ COP) |
| :--- | :--- |
| **Limonada Natural** | $7.700 |
| **Limonada de Coco** | $9.900 |
| **Limonada Cherry** | $9.900 |
| **Jugo de Mandarina** | $8.300 |
| **Jugos en Agua** | $8.000 |
| **Jugos en Leche** | $9.000 |
| **Gaseosa Personal** | $5.500 |
| **Gaseosa 1.1/4 Litro** | $12.000 |
| **Fuze Tea** | $5.500 |
| **Agua en Botella** | $5.000 |
| **Cerveza** | $7.000 |

---

## 3. Estado de la Guía de 18 Fases (README.md)

| Fase | Título | Estado Actual | Pendiente para Mañana |
| :---: | :--- | :---: | :--- |
| 1-3 | Fundación, BD y Auth/Roles | ✅ COMPLETO | Nada, 100% verificado |
| **4** | **Catálogo de Productos** | 🟡 **EN PROCESO** | **Cargar el archivo `02_seeds.sql` con el menú real de Mr. Burger recién transcrito.** |
| 5-16 | Mesero, Realtime, KDS, Caja, Vales, Inventario, DiDi, Egresos, Cierre, Preparados, Admin, Sync | ✅ COMPLETO | 425 pruebas automatizadas pasando (392 backend + 33 E2E frontend). |
| **17** | **Frontend PWA** | 🟡 **AJUSTE MENOR** | **Asegurar que la vista de mesero (`/mesero`) muestre este catálogo en botones compactos y sin miniaturas de fotos**, tal como pidió el cliente. |
| **18** | **Despliegue & Puesta en Marcha** | ⏳ **PENDIENTE** | Configurar arranque en servidor local (LAN Mini PC / Raspberry) y sincronización con nube. |

---

## 4. Tareas Inmediatas para Mañana

1. **Crear `database/init/02_seeds.sql`**:
   - Insertar las categorías reales (`HAMBURGUESAS`, `COMBOS`, `PERROS`, `ASADOS`, `DESGRANADOS Y MAZORCAS`, `ALITAS`, `PARA COMPARTIR / ADICIONES`, `BEBIDAS`).
   - Insertar los 40+ productos con sus precios reales en pesos colombianos.
2. **Levantar Docker y Poblar la BD**:
   - Iniciar Docker Desktop y correr `docker compose up -d` para verificar que la base de datos cargue los datos sin errores de sintaxis.
3. **Verificación Visual en el Frontend**:
   - Validar que el mesero vea la lista de Mr. Burger limpia, rápida y responsiva en mobile.
   - Probar el flujo completo: Crear pedido en mesa → Cocina KDS con campana → Cobro en caja → Impresión de tirilla.

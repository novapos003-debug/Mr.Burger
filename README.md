# Sistema POS Restaurante — Documento Maestro

> **"SIMPLE POR FUERA. INTELIGENTE POR DENTRO."**
> El mesero toca botones, la cocina recibe solo, el inventario se descuenta por recetas
> y el dueño ve su negocio desde el celular.

Este documento es la **fuente de verdad** de la idea, el alcance y el plan del proyecto.
Si una decisión no está aquí, se discute antes de codificar. Nada se borra: se registra.

---

## Índice

1. [La idea](#1-la-idea)
2. [Equipos y usuarios del local](#2-equipos-y-usuarios-del-local)
3. [Arquitectura técnica](#3-arquitectura-técnica)
4. [Los 4 canales de venta](#4-los-4-canales-de-venta)
5. [Estados del sistema](#5-estados-del-sistema)
6. [Reglas de negocio críticas](#6-reglas-de-negocio-críticas)
7. [Flujos principales](#7-flujos-principales)
8. [Preparados (reventa de producidos)](#8-preparados-reventa-de-producidos)
9. [Modelo de datos (MER v4)](#9-modelo-de-datos-mer-v4)
10. [Plan de desarrollo — 18 fases](#10-plan-de-desarrollo--18-fases)
11. [MVP vs Futuro](#11-mvp-vs-futuro)
12. [Estado actual de implementación](#12-estado-actual-de-implementación)
13. [Hardware](#13-hardware)
14. [Anexo A — Prompts para presentación al cliente](#anexo-a--prompts-para-presentación-al-cliente)

---

## 1. La idea

Sistema **POS completo para un restaurante de comida rápida en Cali**, que cubre los cuatro
roles operativos:

- **Meseros** — tomar pedidos en mesa y agregar rondas.
- **Cocina (KDS)** — tickets en pantalla, temporizador e inventario.
- **Caja** — cobros, vales, devoluciones, turno y cierre.
- **Admin (dueño)** — dinero, catálogo, inventario, reportes, entradas/egresos.

Canales de venta: **mesas, mostrador, DiDi y domicilio**.

---

## 2. Equipos y usuarios del local

| Rol | Dispositivo | Cantidad |
|-----|-------------|----------|
| Mesero | Android | 4 |
| Caja | Windows o Android | 1 |
| Cocina | Android | 1 |
| Admin (dueño) | iPad / cualquier navegador | 1 |
| Impresora | Térmica 80mm ESC/POS (caja) | 1 |

Máximo **~10 dispositivos** conectados a la vez.

---

## 3. Arquitectura técnica

**"Cerebro local" en el restaurante** (no en la nube). El local trabaja 100% contra su
servidor interno por red LAN; la nube es un espejo para el admin.

```
        ⌂ INTERIOR DEL LOCAL (funciona SIN internet)
  ┌────────────────────────────────────────────────┐
  │  ROUTER WI-FI (misma red)                       │
  │        │                                        │
  │  ┌─────┴──────────┐                             │
  │  │  CEREBRO LOCAL  │  mini PC / Raspberry / PC   │
  │  │  (Postgres +    │  siempre encendido          │
  │  │   Backend)      │  IP local fija (192.168.1.50)
  │  └─────┬──────────┘                             │
  │        │                                        │
  │  ┌─────┼──────┬───────┐                         │
  │  │     │      │       │                         │
  │ MESERO MESERO COCINA  CAJA                      │
  └────────┴──────┴───────┴─────────────────────────┘
        │ (solo cuando hay internet)
        ▼
   ☁️ NUBE (espejo del admin)
      · al volver internet, el cerebro local sube todo
      · y baja lo que el admin cambió desde afuera
```

**Decisiones clave:**

- **PWA en React + Vite + Tailwind**: un solo código para Android, Windows, iPad y web.
- **FastAPI + PostgreSQL**; **WebSockets** para pedido→cocina instantáneo.
- **Sin internet el local sigue vendiendo**: mesero → cocina → caja siguen en vivo por red interna.
  El internet solo se necesita para **sincronizar con la nube** (que el admin vea desde afuera).
- **Sincronización bidireccional** cerebro-local ↔ nube, en orden, con **ID único de operación**
  por dispositivo (sin duplicados). Autoridad: lo que **vende** manda el **local**; lo que
  **configura** el admin baja de la **nube**.
- **Fotos**: se suben al backend (WebP comprimido) y un evento "catálogo actualizado" las reparte
  a los 10 equipos, con caché local para offline.
- **Impresión**: WebUSB (igual en Windows y Android), cualquier térmica 80mm.
- El "cerebro local" es **el mismo paquete docker-compose** que se instala en la nube.

---

## 4. Los 4 canales de venta

| Canal | Flujo |
|-------|-------|
| **MESA (1-9)** | pedido + rondas → pago al final → mesa libre |
| **MOSTRADOR** | cobra adelantado → cocina → entrega con ticket |
| **DOMICILIO** | nombre, teléfono, dirección → cocina → pago al recibir o pagado |
| **DIDI** | número de orden DiDi → cocina → `DIDI_TARJETA` (consignan) o `DIDI_EFECTIVO` (el repartidor paga en el local) |

---

## 5. Estados del sistema

**Pedido:**
`NUEVO → ENVIADO_A_COCINA → EN_PREPARACION → FINALIZADO → ENTREGADO → PAGADO → CERRADO`
(+ `CANCELADO`, solo admin)

**Línea de pedido (ronda):**
`ENVIADO → PREPARANDO → LISTO → ENTREGADO → CANCELADO`

**Mesa:**
- 🟢 `DISPONIBLE`
- 🟡 `EN_CURSO` (comida en producción)
- 🔴 `OCUPADA` (cuenta servida / en pago)

**Rondas:** cada ronda que el cliente pide después va a cocina como **ticket propio** con su hora
y temporizador (**28 min configurable**).

---

## 6. Reglas de negocio críticas

| Regla | Decisión final |
|-------|----------------|
| **Inventario se descuenta** | Cuando la cocina **ACEPTA → EN PREPARACIÓN** (producción real), no al enviar ni al pagar |
| **Cancelar pedido** | **Solo admin**. Si pagó → devolución del dinero en caja |
| **Cancelar + no producido** | No se descuenta nada (nunca se gastó insumo) |
| **Cancelar + producido** | Los insumos se mantienen descontados (ya se consumieron) |
| **Preparados** | El producido cancelado queda `DISPONIBLE` para revender (hasta que el admin lo descarte) |
| **Vale (pagaré)** | Nombre, cédula, teléfono, hora, qué comió, monto. Estado `PENDIENTE`/`COBRADO`. Admin y caja lo cobran |
| **Egresos / entradas de dinero** | **Solo admin**, con **descripción obligatoria** (pago turno, préstamo, adelanto, cambio inicial…) |
| **DiDi tarjeta** | En ventas queda "por cobrar de DiDi" (consignación) — **NO** es efectivo |
| **DiDi efectivo** | El repartidor entrega la plata → **sí** es efectivo físico del turno |
| **IVA** | 19% configurable, **incluido** en el precio; el recibo separa `subtotal / IVA / total` |
| **Disponibilidad** | Automática: si algún insumo de la receta no alcanza → NO DISPONIBLE (o manual del admin) |
| **Visibilidad de dinero** | Mesero y cocina **NO ven dinero**, ni márgenes/costos/inventario. Solo admin ve todo |

### 6.1 Regla final de cancelación (tabla definitiva)

El botón **CANCELAR** solo es visible para el **admin** (la caja no cancela, solo devuelve el dinero
físico). El ancla es **producido o no producido** (`EN PREPARACIÓN` en cocina), **no** el pago ni la
entrega:

| Momento de la cancelación | ¿Devuelve dinero? | Inventario |
|---------------------------|-------------------|------------|
| No pagado + no producido | No | No se descuenta (nunca se gastó) |
| No pagado + producido | No | Se mantiene descontado (ya se gastó) |
| Pagado + no producido | **Sí, en caja** | No se descuenta (nunca se gastó) |
| Pagado + producido | **Sí, en caja** | Se mantiene descontado (ya se gastó) |

En todos los casos:

1. El admin **autoriza y registra** la cancelación con **motivo** (queda en el historial para siempre).
2. Si hubo pago, el dinero se entrega en caja (**movimiento de caja SALIDA de devolución** con
   descripción: *"devolución pedido #X, motivo…"*).
3. El inventario **sigue siempre la producción real, nunca la plata**. No hay insumos "mágicos".

**Regla de oro:** nada se borra. Cancelar = evento con **motivo** y **reversa**, no eliminación.
El historial es la ley.

---

## 7. Flujos principales

### Flujo A — Pedido en mesa
```
Mesero: canal MESA → mesa # → fotos → cantidades → ENVIAR
  → mesa 🟡 · cocina recibe ticket (mesa, hora, ⏱ 28') · inventario descuenta al ACEPTAR
  → cocina FINALIZADO → mesero entrega → mesa 🔴
  → cliente pide más → ronda 2 → vuelve a cocina → se suma a la cuenta
  → caja cobra (método, cambio) → libera mesa 🟢 → recibo → cierre/inventario/estadísticas
```

### Flujo B — Cancelación (solo admin)
```
Admin cancela → motivo obligatorio (historial)
  ¿Pagó?        → caja devuelve dinero (MOVIMIENTO_CAJA salida + descripción)
  ¿Producido?   → NO toca inventario (se mantiene descontado)
                  → sus líneas pasan a PREPARADOS (para revender)
  ¿No producido?→ no se descuenta nada
```

### Flujo C — Reventa de preparado
```
Mesero ve "🥡 PREPARADOS (2)" → ve producto + modificaciones + hace cuánto
  → el sistema sugiere cuando coincide producto+mods → mesero acepta
  → ASIGNADA (reservada, nadie más la usa) · ticket "USAR PREPARADO"
  → NO se descuenta inventario (ya estaba gastado) · se cobra cuando el cliente paga
  → si no se reutiliza: el admin la DESCARTA (control de desperdicio)
```

### Flujo D — DiDi Food
```
Cliente pide en app DiDi → llega a DiDi Tienda (app de ellos)
  → Caja registra en nuestro sistema: canal DIDI + #orden + método
  → Cocina prepara (descuenta insumos) → código de verificación → repartidor
  → DIDI_TARJETA: sale del cierre como "por cobrar DiDi"
  → DIDI_EFECTIVO: el repartidor deja la plata → entra al efectivo de caja
```

### Flujo E — Cierre de turno (lo que se imprime)
```
PEDIDOS atendidos · VENTA comida / bebidas
PAGOS: efectivo · tarjeta · transferencia · vales (cantidad)
ENTRADAS/SALIDAS de caja (solo admin, con descripción)
DIDI: por cobrar · efectivo entregado por repartidor
DEVOLUCIONES (si hubo) · PREPARADOS reutilizados/descartados
TOTAL VENTAS → TOTAL EFECTIVO EN CAJA → TOTAL POR COBRAR (DiDi + vales)
```

---

## 8. Preparados (reventa de producidos)

Cuando un pedido **producido** se cancela, la comida **no se bota**: pasa a una "bolsa de
preparados disponibles", caliente y visible "para retomar". Si llega otro cliente que pide lo mismo,
se asigna en vez de producirla de nuevo → **no se descuenta inventario por segunda vez**.

### Reglas finales

1. **Duración:** un preparado queda `DISPONIBLE` **hasta que el admin lo descarte**. No hay
   temporizador automático. El sistema muestra **cuánto lleva esperando** ("hace 12 min") para que el
   mesero lo ofrezca con honestidad y el dueño decida cuándo descartar.
2. **El mesero los ve y los recomienda:** sección "PREPARADOS" siempre visible con producto + foto +
   **los añadidos/modificaciones** que pidió el cliente original (doble carne, sin tomate, queso extra…).
   Con un toque lo agrega al pedido en curso → cae con nota interna **"USAR PREPARADO"** (cocina solo
   calienta; no prepara, no descuenta).
3. **Sugerencia automática:** cuando un mesero arma un pedido que **coincide producto + modificaciones**
   con un preparado libre, el sistema ofrece el atajo: *"Ya existe 1× Hamburguesa Especial (sin tomate)
   lista de un pedido cancelado. ¿La uso y gano 10 min?"* → `[USAR PREPARADO]` / `[PREPARAR NUEVA]`.
4. **Protección contra choque de meseros:** al tocar "USAR" se marca `ASIGNADO` en la **misma
   transacción**. El segundo mesero recibe *"ya fue asignada"*. Imposible vender dos veces la misma
   hamburguesa (un preparado solo puede estar `DISPONIBLE`; al asignarse queda reservado).
5. **Si el pedido que la usó también se cancela** (y estaba producido) → vuelve a `DISPONIBLE`
   (reingresa a la bolsa; no se descuenta dos veces).
6. **Cierre de turno** agrega la línea: `PREPARADOS: reutilizados N · descartados M` (+ cuánto lleva
   en espera el más antiguo), para que el dueño vea si la comida "rueda" o se está descartando.

### Cómo impacta dinero e inventario
- El descuento de insumos ocurrió **al producir**: ese consumo queda **una sola vez**.
- La venta (ingreso) ocurre **al pagar**: la reventa genera ingreso **sin nuevo costo directo**.
- Corte del día: **1 producción = 1 costo, 1 pago = 1 ingreso**. Cuadra perfecto.

### Lo que ve la cocina
El ticket del nuevo pedido llega con la nota: **"USAR PREPARADO (1× Hamburguesa Especial)"** en vez
de prepararla; el de cocina solo la calienta y sabe que no descontó nada nuevo.

### Modelo de datos

```
PREPARADO {
  int id PK
  int producto_id FK
  int pedido_origen_id FK          "pedido cancelado y producido"
  int detalle_origen_id FK         "la línea exacta que se cocinó"
  string variacion_snapshot        "JSON: modificaciones (doble carne, sin tomate)"
  decimal cantidad                 "1"
  string estado                    "DISPONIBLE | ASIGNADO | DESCARTADO"
  int pedido_nuevo_id FK           "nulable: quién lo reutilizó"
  int usuario_id FK                "quién asignó o descartó"
  datetime creado_en
  datetime asignado_en
  datetime descartado_en
}
```

`variacion_snapshot` guarda los añadidos tal cual se pidieron: sirve para mostrárselos al mesero y
para la **coincidencia automática**.

---

## 9. Modelo de datos (MER v4)

```
USUARIO → ROL                        (admin / cajero / mesero / cocina)
CATEGORIA → TIPO_CATEGORIA           (COMIDA / BEBIDA) → PRODUCTO
PRODUCTO → DETALLE_RECETA → INGREDIENTE      (receta con fracciones)
INGREDIENTE → MOVIMIENTO_INVENTARIO  (VENTA / COMPRA / MERMA / AJUSTE)
MESA → PEDIDO → DETALLE_PEDIDO (rondas) → PRODUCTO
PEDIDO → PAGO                        (efectivo / tarjeta / transferencia / vale / didi×2)
PEDIDO → VALE                        (pagaré: nombre, cédula, teléfono, monto, estado)
USUARIO → MOVIMIENTO_CAJA            (entradas / salidas, descripción obligatoria)
USUARIO → CIERRE                     (fotograma inmutable del cierre)
PEDIDO → PREPARADO → PRODUCTO        (reventa de producidos)
PROVEEDOR → COMPRA → DETALLE_COMPRA  (V2)
HISTORIAL_ACCION                     (nadie toca nada sin registro)
```

**Regla de oro:** nada se borra. Cancelar = evento con motivo y reversa, no eliminación.

---

## 10. Plan de desarrollo — 18 fases

Cada fase entrega algo **probable de forma vertical**: un ciclo completo que funciona de punta a
punta antes de pasar a la siguiente.

| # | Fase | Qué | Por qué en este orden |
|---|------|-----|-----------------------|
| 1 | Fundación | Repo, monorepo, docker-compose (Postgres + FastAPI) corriendo | Sin esto nada más existe |
| 2 | Base de datos | SQL definitivo, migraciones, seeds de prueba | El MER ya está cerrado: es el contrato |
| 3 | Auth y roles | Login, JWT, permisos duros por rol | Define quién puede qué desde el día 1 |
| 4 | Catálogo | Productos, categorías, fotos, precios, IVA | Sin catálogo no se pide nada |
| 5 | Mesero | Canales, mesas 1-9, carrito, cantidades, rondas, ENVIAR | Es el primer ciclo completo |
| 6 | Realtime | WebSocket: pedido→cocina en 1s, mesa cambia, estados | La magia que impresiona al dueño |
| 7 | Cocina KDS | Tickets, mesa/dirección, hora, temporizador 28', ACEPTAR/EN PREPARACIÓN/FINALIZADO | Cierra el ciclo mesero→cocina→mesero |
| 8 | Caja | Cuenta en curso, pagos, cambio, métodos, recibo con IVA, impresión WebUSB | Cierra el ciclo de dinero |
| 9 | Vales | Pagaré con datos del fiador, cobro (admin+caja) | Pedido del dueño, reglas claras |
| 10 | Inventario | Recetas, deducción al producir, movimientos, disponibilidad automática | El corazón "inteligente" |
| 11 | Didi | Canal DIDI + dos métodos de pago | Dinero del domicilio cuadrado |
| 12 | Movimientos de caja | Egresos/entradas solo admin con descripción | Control del dinero físico |
| 13 | Cierre de turno | Reporte impreso completo + fotograma inmutable | Al final de cada día, obligatorio |
| 14 | Cancelación + preparados | Solo admin, devolución en caja, reventa | Sobre la base ya estable |
| 15 | Panel admin | Dashboard, movimientos, historial, recetas, precios, stock, gastos | El dueño gobierna desde su iPad |
| 16 | Offline + sync | Cola local, ID único, sin duplicados | La promesa "nunca se para el local" |
| 17 | Pruebas E2E | Los 10 escenarios que ya definimos | Antes de tocar producción |
| 18 | Despliegue | VPS, dominio, instalación en el local, capacitación | El día 1 con clientes de verdad |

**Regla de oro del desarrollo:** cada fase se prueba **en vertical**. Un pedido de mesa debe poder
`enviar → cocina → cobrar → recibo → descontar inventario → aparecer en dashboard`. Solo cuando ese
ciclo completo funciona, se pasa a la siguiente fase.

---

## 11. MVP vs Futuro

**En el MVP (plan 1-18):** canales mesa/mostrador/domicilio/DiDi, rondas, cocina con temporizador,
caja con pagos y recibo, vales, inventario por recetas, disponibilidad, egresos, cierre,
cancelación + preparados, panel admin, offline.

**Fuera del MVP (se agrega después, sin reescribir):** integración automática con DiDi (hoy manual
por la app de ellos), QR de auto-pedido en mesa, fidelización, multi-sucursal, factura DIAN,
control avanzado de merma (conteo vs teórico), exportaciones a Excel.

---

## 12. Estado actual de implementación

> Actualizado tras completar la **Fase 15 (Panel Admin)** y la **Fase 16 (Offline + Sync)**. Todo lo listado abajo está
> **verificado con pruebas automatizadas** (7 suites, **392 PASS / 0 FAIL**, idempotentes: se corren
> dos rondas seguidas y dan el mismo resultado).

### Construido (backend + base de datos)

| Fase del plan | Estado | Evidencia / notas |
|---------------|--------|-------------------|
| 1. Fundación | ✅ | `docker-compose.yml` (Postgres 16 + FastAPI), zona horaria `America/Bogota` |
| 2. Base de datos | ✅ | 22 tablas (incluye `preparado`, `compra`, `detalle_compra`, `registro_sync`), CHECKs y FKs; **`historial_accion` ya se escribe** en cada operación sensible |
| 3. Auth y roles | ✅ | JWT Bearer; roles `admin / cajero / mesero / cocina`; permisos duros |
| 4. Catálogo | ✅ (fotos ❌) | Categorías, productos, precios, IVA, recetas; **faltan fotos** |
| 5. Mesero | ✅ | 4 canales, mesas 1-9, líneas, rondas, enviar a cocina |
| 6. Realtime | ✅ | WebSocket `/ws/pedidos` (con auth por token y sin fuga de dinero) |
| 7. Cocina KDS | ✅ | Cola por ronda, temporizador 28', aceptar/listo, sin precios |
| 8. Caja | ✅ | Cobro multi-método, cambio, pagos; **falta integración hardware WebUSB** |
| 9. Vales | ✅ | Pagaré `PENDIENTE`/`COBRADO` |
| 10. Inventario | ✅ | Descuento al producir + movimientos + **disponibilidad automática aplicada al pedir** + **compras y reabastecimiento a proveedores con costeo unitario y auditoría** ✅ |
| 11. DiDi | ✅ | Canal DIDI + `DIDI_TARJETA` / `DIDI_EFECTIVO` |
| 12. Movimientos de caja | ✅ | Entradas/egresos **solo admin**, descripción obligatoria |
| 13. Cierre de turno | ✅ | Apertura/cierre explícitos, fotograma inmutable con `preparados_reutilizados` y `preparados_descartados`; **falta reporte impreso** |
| 14. Cancelación + preparados | ✅ | Cancelación solo admin con motivo; devolución en caja si pagó; bolsa de preparados reusables; concurrencia segura con lock; cocina no re-descuenta; descarte admin; 55 pruebas E2E pasando |
| 15. Panel admin | ✅ | Dashboard en vivo (KPIs, ventas hoy, ticket promedio, ventas por canal/tipo/método, top productos, alertas stock, preparados, vales), reportes históricos filtrables por rango y canal, stock crítico, gestión de compras a proveedores con afectación de inventario, auditoría e historial de acciones; 41 pruebas E2E pasando |
| 16. Offline + sync | ✅ | Motor de sincronización cerebro local ↔ nube, idempotencia por UUID (sin duplicados ante reintentos de red), regla de autoridad estricta (ventas y caja manda local, catálogo y precios manda nube), resolución de conflictos y log de sync; 26 pruebas E2E pasando |
| 17. Pruebas E2E & Frontend PWA | ✅ | 100% PASS (8 suites de pruebas, **425 casos automáticos** sin fallos); PWA React 19 + Vite 8 + Tailwind v4 + Lucide Icons terminada al 100% (Subfases 17.1 a 17.7) |
| 18. Despliegue | ❌ pendiente | Arquitectura docker idéntica lista para Mini PC local y VPS en nube |

### Frontend PWA (React 19 + TypeScript + Vite + Tailwind CSS) — 100% CONSTRUIDO

La **Fase 17** completó el Frontend PWA y la integración E2E multidisciplinar en **7 subfases modulares**:

1. **Subfase 17.1: Fundación PWA & Login Multirrol (`/login`):**
   - Base con React 19, Vite 8, TypeScript, Tailwind CSS v4, Lucide Icons, React Router v7.
   - PWA con Service Worker (`standalone`) e instalación nativa en Android, iPad y Windows.
   - Autenticación JWT, control de roles (`admin`, `cajero`, `mesero`, `cocina`) y monitor de cerebro LAN en vivo.
2. **Subfase 17.2: Módulo Mesero Móvil (`/mesero`):**
   - Semáforo táctil de Mesas 1 a 9 en tiempo real (Verde: Libre, Amarillo: En cocina, Rojo: Ocupada).
   - Selector de los 4 canales: Mesa, Mostrador, Domicilio (con dirección) y DiDi Food (con # orden).
   - Catálogo por categorías con buscador, indicador de stock y precios visibles.
   - Modal de variaciones: adiciones con precio extra y notas de cocina sin costo.
   - Comanda lateral con soporte para Nuevo Pedido y Rondas adicionales.
3. **Subfase 17.3: Pantalla de Cocina KDS (`/cocina`):**
   - Pantalla horizontal en tiempo real conectada al WebSocket `/ws/pedidos`.
   - Campana sonora de comanda con Web Audio API (*Ding-Dong* nativo sin librerías externas).
   - Temporizador monospace de 28 minutos por ticket con alerta visual según demora.
   - Botones de estado: `ACEPTAR` (descuenta inventario) y `LISTO` (notifica al mesero).
   - Regla estricta: precios y dinero 100% ocultos al personal de cocina.
4. **Subfase 17.4: Caja & Arqueo Ciego (`/caja`):**
   - Apertura de turno con base inicial de caja.
   - Cobro multi-método: Efectivo (cálculo de cambio), Tarjeta datáfono, Transferencia, Vales y DiDi.
   - Módulo de Vales / Pagarés con registro de cliente, teléfono y cédula.
   - Movimientos de caja menor (entradas/salidas) con descripción obligatoria.
   - Arqueo Ciego: conteo de denominaciones a ciegas con cálculo automático de faltante o sobrante.
5. **Subfase 17.5: Impresión Térmica 80mm & Formato de Tirillas:**
   - Driver WebUSB nativo para impresoras térmicas USB estándar (ESC/POS binario).
   - Impresión estándar de navegador / PDF como respaldo.
   - Formatos oficiales de Mr. Burger:
     - Recibo de venta con desglose de ítems, variaciones, subtotal e **IVA 19% incluido**.
     - Comprobante de egreso/retiro de caja menor con **las 3 firmas obligatorias** (`[ ENTREGÓ ]`, `[ RECIBIÓ ]`, `[ AUTORIZÓ ]`) y monto en letras.
     - Reporte Z de cierre de turno con arqueo ciego y fotograma contable inmutable.
6. **Subfase 17.6: Panel de Administración & Dueño (`/admin`):**
   - Dashboard ejecutivo con KPIs en tiempo real (ventas del día, ticket promedio, ventas por canal y método).
   - **Planilla Oficial de Cuadre Diario digitalizada**: reproduce la fórmula manual `Base + Ventas - Compras - Egresos = Saldo en Cajón` con filtros de fechas.
   - Módulo de Compras a Proveedores: registro de facturas, actualización automática de costos unitarios y reabastecimiento de stock.
   - Bolsa de Preparados: visualización de alimentos de órdenes canceladas con minutos de espera y descarte de mermas.
   - Bitácora inmutable de auditoría (`historial_accion`) con filtros de usuario y acción.
7. **Subfase 17.7: Pruebas E2E Integradas Multidispositivo:**
   - Suite completa (`test_e2e_fase17.py`) que simula un turno entero con los 4 roles interactuando en simultáneo: **33 PASS / 0 FAIL**.

### Próxima fase: Despliegue y Puesta en Marcha Final (Fase 18)

La **Fase 18** se organiza en 3 etapas priorizadas de implementación y validación en terreno:

* **Subfase 18.1: Consistencia de Inventario y Políticas de Faltantes (CRÍTICO):**
  - Deducción automática de insumos en caja para órdenes que no pasan por KDS (mostrador y bebidas).
  - Configuración de política de stock insuficiente (`BLOQUEAR` vs `ADVERTIR_Y_PERMITIR`) en la tabla `configuracion`.
  - Visualización del margen de utilidad bruta porcentual en la ficha de producto del panel de administración.
* **Subfase 18.2: Despliegue en Red Local LAN y Android WebAPK (IMPORTANTE):**
  - Asignación de IP fija local en el router (ej. `192.168.1.50`) para el computador de caja / servidor local.
  - Instalación de la app en los celulares Android de meseros y tablet de cocina vía WebAPK (acceso directo, pantalla completa, soporte táctil instantáneo).
  - Validación de la cola de pedidos offline ([`offlineQueue.ts`](file:///C:/Users/jhona/Documents/Default%20Project/frontend/src/utils/offlineQueue.ts)) ante microcortes de señal Wi-Fi.
  - Prueba de actualizaciones Over-The-Air con [`actualizar_sistema.bat`](file:///C:/Users/jhona/Documents/Default%20Project/scripts/actualizar_sistema.bat) y [`UpdateBanner.tsx`](file:///C:/Users/jhona/Documents/Default%20Project/frontend/src/components/common/UpdateBanner.tsx).
  - Simulacro de apagón de Internet: desconectar físicamente la conexión WAN y comprobar 100% de operatividad en salón, cocina y caja.
* **Subfase 18.3: Despliegue Espejo Cloud y Dashboard Remoto del Dueño (NUBE):**
  - Despliegue del contenedor con `MODO_CEREBRO = "NUBE"` en servidor accesible (VPS / Render / Railway).
  - Conexión del worker de sincronización local ([`sync_worker.py`](file:///C:/Users/jhona/Documents/Default%20Project/backend/app/services/sync_worker.py)) con reintentos exponenciales e idempotencia.
  - Indicador de *"Última sincronización: HH:MM"* en el panel del dueño consultado desde fuera del local.

---

## 13. Hardware

- **Cerebro local:** mini PC reacondicionado o Raspberry con SSD (~$400-700k COP).
- **UPS** pequeño para router y cerebro (~$150-250k COP).
- **Impresora** térmica 80mm ESC/POS en caja.
- Una sola inversión: el local queda blindado a cortes prolongados.

---

## Anexo A — Prompts para presentación al cliente

> Las IAs de imagen escriben mal el texto en español. Regla: pedir poco o ningún texto y agregar
> los títulos después (Canva/Figma/Photoshop). Orden sugerido de envío:
> **6 → 2 → 3 → 4 → 5 → 7 → 1** (1 como cierre de conversación).

1. **Concepto "Simple por fuera, inteligente por dentro".** Infografía flat, cálida (rojo/crema/dorado);
   mesero tocando un botón → red de nodos (cocina, caja, inventario, monedas, gráficas) → dashboard.
2. **Flujo visual del pedido.** Dos paneles: teléfono con 6 toques → tres carriles (KDS con timer,
   caja imprimiendo, dashboard con gráficas).
3. **Mockup del celular del mesero.** Selector "MESA 5", categorías con fotos, botón "ENVIAR PEDIDO".
4. **Pantalla de cocina (KDS).** Tarjetas por mesa, temporizador monospace, botones
   ACEPTAR / EN PREPARACIÓN / LISTO, **sin precios**.
5. **Panel del dueño (iPad).** KPIs (Ventas hoy, Pedidos, Ganancia), gráficas, alertas de stock,
   top productos.
6. **"Sin internet no pasa nada".** Isométrico: local con dispositivos conectados a un servidor
   central (líneas sólidas) + nube con línea punteada de sincronización.
7. **Recibo con IVA.** Foto realista de tirilla 80mm con `SUBTOTAL`, `IVA 19%`, `TOTAL`,
   `EFECTIVO RECIBIDO`, `CAMBIO`.

### Mensaje para el cliente

> "Señor, le comparto cómo se ve el sistema que tenemos diseñado: la manera en que su equipo lo va a
> usar, cómo llega el pedido a cocina, y el panel que usted va a ver desde el celular. La última
> imagen es mi favorita: aunque el internet se caiga, adentro del local todo sigue funcionando
> normal — los pedidos, la cocina y la caja. Usted solo necesita internet para ver los números desde
> afuera. ¿Le parecen bien estas pantallas o quiere ajustar algo antes de que empecemos?"

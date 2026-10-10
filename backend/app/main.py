import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.config import settings
from app.core.security import decode_access_token
from app.database import Base, engine, SessionLocal
import app.models  # registra todos los modelos SQLAlchemy
from app.models import Usuario
from app.routers import (
    admin,
    auth,
    caja,
    categorias,
    cocina,
    inventario,
    pedidos,
    preparados,
    productos,
    sync,
    asistencia,
)
from app.services.sync_worker import sync_background_loop
from app.services.websocket import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asegura que todas las tablas de los modelos existan en la BD (incluyendo la nube)
    try:
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE turno_laboral ADD COLUMN IF NOT EXISTS rol VARCHAR(50) NOT NULL DEFAULT 'cajero';"))
            conn.execute(text("ALTER TABLE turno_laboral ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE producto ADD COLUMN IF NOT EXISTS empaque_llevar_id INT REFERENCES producto(id);"))
            conn.execute(text("ALTER TABLE producto ADD COLUMN IF NOT EXISTS manual_disponible BOOLEAN;"))
            conn.execute(text("ALTER TABLE pedido ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100) UNIQUE;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pedido_idempotency_key ON pedido(idempotency_key);"))
            conn.execute(text("ALTER TABLE detalle_pedido ADD COLUMN IF NOT EXISTS clave_idempotencia VARCHAR(100);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_detalle_pedido_clave_idempotencia ON detalle_pedido(clave_idempotencia);"))
            conn.execute(text("ALTER TABLE producto ADD COLUMN IF NOT EXISTS permite_adiciones BOOLEAN NOT NULL DEFAULT TRUE;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movcaja_creado_en ON movimiento_caja (creado_en);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movcaja_cierre ON movimiento_caja (cierre_id);"))

            # Migración 04: Empaques dinámicos, bolsas T20-T40, saneamiento de catálogo y gastos operativos
            conn.execute(text("ALTER TABLE detalle_receta ADD COLUMN IF NOT EXISTS solo_llevar BOOLEAN NOT NULL DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS tipo_articulo VARCHAR(30) DEFAULT 'INSUMO_RECETA';"))
            conn.execute(text("ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS precio_venta NUMERIC(12, 2) DEFAULT 0;"))
            conn.execute(text("ALTER TABLE pedido ADD COLUMN IF NOT EXISTS tipo_consumo VARCHAR(15) DEFAULT 'LOCAL';"))
            conn.execute(text("ALTER TABLE pedido ADD COLUMN IF NOT EXISTS recargo_empaque NUMERIC(12, 2) DEFAULT 0;"))
            # Restricciones CHECK: el esquema original las creó con nombre automático
            # (<tabla>_<columna>_check) y sin los valores nuevos. Si solo se agrega la nueva, la
            # vieja sigue rechazando GASTO_OPERATIVO / ANULADO. Se eliminan ambas y se recrea una.
            conn.execute(text("ALTER TABLE movimiento_caja DROP CONSTRAINT IF EXISTS movimiento_caja_categoria_check;"))
            conn.execute(text("ALTER TABLE movimiento_caja DROP CONSTRAINT IF EXISTS ck_movcaja_categoria;"))
            conn.execute(text("ALTER TABLE movimiento_caja ADD CONSTRAINT ck_movcaja_categoria CHECK (categoria IN ('PAGO_TURNO','PRESTAMO','ADELANTO','PROVEEDOR','DEVOLUCION','COBRO_VALE','CAMBIO_INICIAL','GASTO_OPERATIVO','OTRO'));"))
            conn.execute(text("ALTER TABLE vale DROP CONSTRAINT IF EXISTS vale_estado_check;"))
            conn.execute(text("ALTER TABLE vale DROP CONSTRAINT IF EXISTS ck_vale_estado;"))
            conn.execute(text("ALTER TABLE vale ADD CONSTRAINT ck_vale_estado CHECK (estado IN ('PENDIENTE','COBRADO','ANULADO'));"))
            # Asegurar categorías de insumo 8 y 10
            conn.execute(text("INSERT INTO categoria_insumo (id, nombre, descripcion, activo) VALUES (8, 'DESECHABLES_EMPAQUES', 'Contenedores C1, P1, bolsas T20-T40, vasos y servilletas', TRUE) ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre;"))
            conn.execute(text("INSERT INTO categoria_insumo (id, nombre, descripcion, activo) VALUES (10, 'GASTOS_OPERATIVOS', 'Artículos de aseo, papelería y mantenimiento', TRUE) ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre;"))
            # Inserción de Bolsas T20 a T40 y Papel de cocina
            conn.execute(text("""
                INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, precio_venta, activo)
                SELECT 'Bolsa T20 (Para Llevar Pequeña)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 100.00, 0.00, TRUE
                WHERE NOT EXISTS (SELECT 1 FROM ingrediente WHERE nombre ILIKE '%Bolsa T20%');
            """))
            conn.execute(text("""
                INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, precio_venta, activo)
                SELECT 'Bolsa T25 (Para Llevar Mediana)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 150.00, 0.00, TRUE
                WHERE NOT EXISTS (SELECT 1 FROM ingrediente WHERE nombre ILIKE '%Bolsa T25%');
            """))
            conn.execute(text("""
                INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, precio_venta, activo)
                SELECT 'Bolsa T30 (Para Llevar Grande)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 200.00, 0.00, TRUE
                WHERE NOT EXISTS (SELECT 1 FROM ingrediente WHERE nombre ILIKE '%Bolsa T30%');
            """))
            conn.execute(text("""
                INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, precio_venta, activo)
                SELECT 'Bolsa T40 (Para Llevar Extra Grande)', 8, 'DESECHABLE_SERVICIO', 'UNIDAD', 300.00, 0.00, TRUE
                WHERE NOT EXISTS (SELECT 1 FROM ingrediente WHERE nombre ILIKE '%Bolsa T40%');
            """))
            conn.execute(text("""
                INSERT INTO ingrediente (nombre, categoria_insumo_id, tipo_articulo, unidad_base, costo_unitario, precio_venta, activo)
                SELECT 'Papel de cocina', 10, 'GASTO_OPERATIVO', 'UNIDAD', 3500.00, 0.00, TRUE
                WHERE NOT EXISTS (SELECT 1 FROM ingrediente WHERE nombre ILIKE '%Papel de cocina%');
            """))
            # Valores iniciales que el admin puede cambiar después: se aplican UNA sola vez.
            # Antes corrían en cada arranque y deshacían los ajustes hechos desde el panel.
            from app.services.migraciones import aplicar_valores_iniciales

            aplicar_valores_iniciales(conn)

            # Poblar recetas base oficiales para productos que no tengan receta configurada
            try:
                from app.services.seed_recetas import sembrar_recetas_base
                sembrar_recetas_base(conn)
            except Exception as err_recetas:
                import logging
                logging.warning("Aviso al sembrar recetas base: %s", err_recetas)

            conn.commit()
    except Exception as e:
        import logging
        logging.error("Aviso al verificar esquema inicial en lifespan: %s", e)

    # Migraciones de cuentas demo/fijadas y empaques (transacción propia: no dependen del bloque anterior)
    try:
        from app.services.migraciones import completar_empaques_llevar, migrar_demo_y_fijados

        with engine.begin() as conn_mig:
            migrar_demo_y_fijados(conn_mig)
        with engine.begin() as conn_emp:
            completar_empaques_llevar(conn_emp)
    except Exception as e_mig:
        import logging
        logging.error("Error aplicando migraciones demo/empaques: %s", e_mig)

    # Preparación de la sincronización por filas
    try:
        from app.core import replicacion
        from app.services.sync import espejo_id, instalacion_id

        with engine.begin() as conn_sync:
            conn_sync.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_registro_sync_fila ON registro_sync (entidad, entidad_uuid);"
            ))
            conn_sync.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_registro_sync_cola ON registro_sync (origen, estado, id);"
            ))
            if settings.MODO_CEREBRO == "NUBE":
                # Lo creado en el panel web se numera desde 1.000.000: nunca choca con la caja
                replicacion.reservar_rango_nube(conn_sync)
                espejo_id(conn_sync)
            else:
                replicacion.ajustar_secuencias_locales(conn_sync)
                instalacion_id(conn_sync)
    except Exception as e_sync:
        import logging
        logging.error("Error preparando la sincronización: %s", e_sync)

    worker_task = None
    if settings.MODO_CEREBRO != "NUBE":
        worker_task = asyncio.create_task(sync_background_loop())
    yield
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


_EN_NUBE = settings.MODO_CEREBRO == "NUBE"

app = FastAPI(
    title="Restaurante API",
    version="0.2.0",
    description="SIMPLE POR FUERA. INTELIGENTE POR DENTRO.",
    lifespan=lifespan,
    # En internet no se publica el mapa de la API; en la red local sigue disponible en /docs
    docs_url=None if _EN_NUBE else "/docs",
    redoc_url=None if _EN_NUBE else "/redoc",
    openapi_url=None if _EN_NUBE else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mrburger-pos-cali.web.app",
        "https://mrburger-pos-cali.firebaseapp.com",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|172\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router unificado con prefijo /api para clientes web / móviles que apuntan a /api
api_router = APIRouter(prefix="/api")

routers_list = [
    auth.router,
    categorias.router,
    productos.router,
    inventario.router,
    pedidos.router,
    cocina.router,
    caja.router,
    preparados.router,
    admin.router,
    sync.router,
    asistencia.router,
    inventario.combo_alias_router,
    admin.configuracion_alias_router,
]

for r in routers_list:
    app.include_router(r)
    api_router.include_router(r)

app.include_router(api_router)


@app.websocket("/ws/pedidos")
async def websocket_pedidos(websocket: WebSocket, token: str | None = None):
    """Canal en tiempo real: cocina y caja reciben los tickets sin recargar.
    Requiere token válido (?token=<jwt>); sin él la conexión se rechaza."""
    payload = decode_access_token(token) if token else None
    if not payload or not payload.get("sub"):
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        usuario = db.get(Usuario, int(payload["sub"]))
        if not usuario or not usuario.activo:
            await websocket.close(code=1008)
            return
    finally:
        db.close()

    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # mantiene la conexión abierta
            if data == "ping":
                await websocket.send_text("pong")
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/health", tags=["sistema"])
@app.get("/api/health", tags=["sistema"])
def health():
    """Healthcheck para Docker y monitoreo de la red local."""
    return {"status": "ok", "sistema": "restaurante", "version": "0.2.0", "modo": settings.MODO_CEREBRO, "entorno": settings.ENTORNO}


@app.get("/", tags=["sistema"])
def root():
    return {"sistema": "Restaurante API", "mensaje": "SIMPLE POR FUERA. INTELIGENTE POR DENTRO."}
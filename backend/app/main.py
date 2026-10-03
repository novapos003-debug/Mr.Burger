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
            conn.execute(text("ALTER TABLE pedido ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100) UNIQUE;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pedido_idempotency_key ON pedido(idempotency_key);"))
            conn.execute(text("ALTER TABLE producto ADD COLUMN IF NOT EXISTS permite_adiciones BOOLEAN NOT NULL DEFAULT TRUE;"))
            conn.commit()
    except Exception as e:
        import logging
        logging.error("Aviso al verificar esquema inicial en lifespan: %s", e)

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


app = FastAPI(
    title="Restaurante API",
    version="0.1.0",
    description="SIMPLE POR FUERA. INTELIGENTE POR DENTRO.",
    lifespan=lifespan,
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
    return {"status": "ok", "sistema": "restaurante", "version": "0.1.0", "entorno": settings.ENTORNO}


@app.get("/", tags=["sistema"])
def root():
    return {"sistema": "Restaurante API", "mensaje": "SIMPLE POR FUERA. INTELIGENTE POR DENTRO."}
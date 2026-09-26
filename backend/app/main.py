import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.security import decode_access_token
from app.database import SessionLocal
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
)
from app.services.sync_worker import sync_background_loop
from app.services.websocket import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia el daemon de sincronización automática en segundo plano
    worker_task = asyncio.create_task(sync_background_loop())
    yield
    # Cancela ordenadamente el daemon al apagar el servidor
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
    allow_origins=["*"],  # en producción restringir al dominio
    allow_origin_regex=".*",  # dev: tablets del local conectan desde cualquier IP LAN
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
            await websocket.receive_text()  # mantiene la conexión abierta
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
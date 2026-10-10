import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import admin_required
from app.core.security import decode_access_token
from app.database import get_db
from app.models import Usuario
from app.schemas.sync import (
    SyncCambiosOut,
    SyncConfirmarIn,
    SyncEstadoOut,
    SyncOpOut,
    SyncPushIn,
    SyncPushOut,
    SyncReiniciarIn,
)
from app.services.sync import (
    TABLAS_CATALOGO,
    confirmar_bajada,
    espejo_id,
    instalacion_vinculada,
    obtener_cambios_nube,
    obtener_estado_sync,
    obtener_pull,
    procesar_push,
    reiniciar_espejo,
)
from app.services.sync_worker import ejecutar_ciclo_sync
from app.services.websocket import ws_manager

router = APIRouter(prefix="/sync", tags=["sync"])


def _token_valido(sync_token: str | None) -> bool:
    esperado = settings.CLOUD_SYNC_TOKEN or ""
    return bool(sync_token) and bool(esperado) and secrets.compare_digest(sync_token, esperado)


def sync_token_required(sync_token: str | None = Header(None, alias="X-Sync-Token")) -> None:
    """Solo la caja, con el token de sincronización. Estos endpoints leen y escriben filas
    completas de cualquier tabla: una sesión de usuario normal NO debe poder usarlos."""
    if not _token_valido(sync_token):
        raise HTTPException(status_code=401, detail="Token de sincronización inválido o no configurado")


def sync_or_staff_required(
    request: Request,
    db: Session = Depends(get_db),
    sync_token: str | None = Header(None, alias="X-Sync-Token"),
) -> Usuario | None:
    """Consulta de estado: el token de sincronización o cualquier usuario con sesión activa."""
    if _token_valido(sync_token):
        return None
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Se requiere autenticación o X-Sync-Token válido")
    payload = decode_access_token(auth_header.split(" ", 1)[1])
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    usuario = db.get(Usuario, int(payload["sub"]))
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario inactivo o inexistente")
    return usuario


@router.get("/health")
def sync_health():
    """Endpoint liviano para verificar conectividad entre servidor local y la nube."""
    return {
        "status": "ok",
        "cerebro_modo": settings.MODO_CEREBRO,
        "sucursal_id": settings.SUCURSAL_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/push", response_model=SyncPushOut)
async def sincronizar_push(
    data: SyncPushIn,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(sync_token_required),
):
    """Recibe de la caja un lote de filas para reflejar en el espejo.

    Idempotente por `op_id`. Cada operación se aplica aislada; si alguna falla el lote responde
    HTTP 207 con el detalle por operación en `resultados` y las demás quedan aplicadas."""
    if settings.MODO_CEREBRO != "NUBE":
        raise HTTPException(status_code=409, detail="Este servidor no es un espejo: no recibe operaciones")
    try:
        # En un hilo aparte: un lote grande tarda, y aquí bloquearía a todo el servidor
        # (el panel web y hasta el chequeo de conexión de la propia caja).
        resultado, tablas = await run_in_threadpool(procesar_push, db, data)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if resultado.errores:
        response.status_code = 207
    if tablas:
        # Quien tenga abierto el panel web lo ve actualizarse en el momento
        await ws_manager.broadcast(
            {"evento": "datos_sincronizados", "data": {"origen": "LOCAL", "tablas": sorted(tablas)}}
        )
        if tablas & TABLAS_CATALOGO:
            await ws_manager.broadcast({"evento": "catalogo_actualizado", "data": {"tipo": "sincronizacion"}})
    return resultado


@router.get("/cambios", response_model=SyncCambiosOut)
def cambios_para_la_caja(
    despues_de: int = Query(default=0, ge=0),
    limite: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: None = Depends(sync_token_required),
):
    """Cambios hechos en el panel web que la caja aún no ha aplicado, en orden."""
    identificador = espejo_id(db.connection())
    db.commit()
    return SyncCambiosOut(
        espejo_id=identificador,
        vinculada=instalacion_vinculada(db.connection()),
        operaciones=obtener_cambios_nube(db, despues_de, limite),
    )


@router.post("/confirmar")
def confirmar_cambios_aplicados(
    data: SyncConfirmarIn,
    db: Session = Depends(get_db),
    _: None = Depends(sync_token_required),
):
    """La caja confirma hasta qué operación del panel web ya aplicó."""
    return {"status": "ok", "confirmadas": confirmar_bajada(db, data.hasta_id)}


@router.post("/reiniciar-espejo")
async def reiniciar_espejo_endpoint(
    data: SyncReiniciarIn,
    db: Session = Depends(get_db),
    _: None = Depends(sync_token_required),
):
    """Vacía el espejo para reconstruirlo desde la caja. Acción deliberada: exige confirmación escrita."""
    if data.confirmar != "REINICIAR ESPEJO":
        raise HTTPException(status_code=422, detail="Para reiniciar el espejo envía confirmar='REINICIAR ESPEJO'")
    try:
        resultado = reiniciar_espejo(db)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    await ws_manager.broadcast({"evento": "datos_sincronizados", "data": {"origen": "REINICIO", "tablas": []}})
    return {"status": "ok", **resultado}


@router.get("/pull", response_model=list[SyncOpOut])
def sincronizar_pull(
    since: datetime | None = None,
    origen: str | None = Query(default=None, pattern="^(LOCAL|NUBE)$"),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Consulta del registro de operaciones para diagnóstico (solo administrador)."""
    return obtener_pull(db, since, origen, limit)


@router.get("/estado", response_model=SyncEstadoOut)
def ver_estado_sync(
    db: Session = Depends(get_db),
    _: Usuario | None = Depends(sync_or_staff_required),
):
    """Estado del motor de sincronización: pendientes, última entrega y último error."""
    return obtener_estado_sync(db, modo=settings.MODO_CEREBRO)


@router.post("/forzar")
async def forzar_sincronizacion_endpoint(
    _: Usuario | None = Depends(sync_or_staff_required),
):
    """Dispara inmediatamente un ciclo de sincronización manual sin esperar el temporizador."""
    resultado = await ejecutar_ciclo_sync()
    return {"status": "ok", "worker_estado": resultado}

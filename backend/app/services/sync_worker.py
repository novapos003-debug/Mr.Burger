import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import func

from app.config import settings
from app.database import SessionLocal, safe_commit
from app.models.sync import RegistroSync

logger = logging.getLogger("sync_worker")

# Estado reactivo en memoria del worker de sincronización
_worker_status: dict[str, Any] = {
    "online": True,
    "sincronizando": False,
    "pendientes": 0,
    "aplicadas": 0,
    "ultima_sincronizacion": None,
    "ultimo_error": None,
    "ultimo_chequeo": None,
}


def get_worker_status() -> dict[str, Any]:
    """Retorna una copia del estado actual del worker de sincronización."""
    return dict(_worker_status)


async def ejecutar_ciclo_sync() -> dict[str, Any]:
    """Ejecuta un ciclo de sondeo y sincronización con el servidor espejo en la nube.
    
    Flujo:
    1. Si estamos en modo NUBE, el servidor es receptor; no envía push hacia afuera.
    2. Consulta cuántos registros PENDIENTES existen en la BD local.
    3. Si no hay CLOUD_SYNC_URL configurada, asume funcionamiento local normal.
    4. Si hay CLOUD_SYNC_URL, hace ping ligero al endpoint /sync/health.
    5. Si hay internet y registros pendientes, envía lotes de hasta 50 operaciones con UUID idempotente.
    6. Actualiza atómicamente el estado local a APLICADO y sincronizado_en = now().
    """
    # Si estamos en modo NUBE o la sincronización está deshabilitada, el worker no debe hacer nada
    if settings.MODO_CEREBRO == "NUBE" or not settings.CLOUD_SYNC_ENABLED:
        _worker_status["online"] = True
        return dict(_worker_status)

    _worker_status["ultimo_chequeo"] = datetime.now(timezone.utc).isoformat()

    # 1. Contar pendientes locales
    db = SessionLocal()
    try:
        p_count = (
            db.query(func.count(RegistroSync.id))
            .filter(RegistroSync.estado == "PENDIENTE")
            .scalar()
            or 0
        )
        _worker_status["pendientes"] = int(p_count)
    except Exception as e:
        logger.warning(f"Error al contar registros pendientes: {e}")
    finally:
        db.close()

    # Si no hay URL de nube configurada (modo local puro de desarrollo o caja única sin nube)
    if not settings.CLOUD_SYNC_URL:
        _worker_status["online"] = True
        _worker_status["ultimo_error"] = None
        return dict(_worker_status)

    # 2. Verificar conectividad con la nube
    cloud_url = settings.CLOUD_SYNC_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{cloud_url}/sync/health")
            if resp.status_code == 200:
                _worker_status["online"] = True
                _worker_status["ultimo_error"] = None
            else:
                _worker_status["online"] = False
                _worker_status["ultimo_error"] = f"Cloud respondió HTTP {resp.status_code}"
                return dict(_worker_status)
    except Exception as e:
        _worker_status["online"] = False
        _worker_status["ultimo_error"] = "Sin conexión a la nube (Operando en Modo Local autónomo)"
        return dict(_worker_status)

    # 3. Si hay internet y hay pendientes, procesar lote
    if _worker_status["pendientes"] > 0:
        db = SessionLocal()
        try:
            pendientes = (
                db.query(RegistroSync)
                .filter(RegistroSync.estado == "PENDIENTE")
                .order_by(RegistroSync.id.asc())
                .limit(50)
                .all()
            )
            if pendientes:
                _worker_status["sincronizando"] = True
                lote = {
                    "dispositivo_id": settings.SUCURSAL_ID,
                    "operaciones": [
                        {
                            "op_id": r.op_id,
                            "sucursal_id": r.sucursal_id,
                            "dispositivo_id": r.dispositivo_id,
                            "tipo": r.tipo,
                            "entidad": r.entidad,
                            "entidad_id": r.entidad_id,
                            "entidad_uuid": r.entidad_uuid,
                            "payload": r.payload,
                            "origen": "LOCAL",
                        }
                        for r in pendientes
                    ],
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    push_resp = await client.post(
                        f"{cloud_url}/sync/push",
                        headers={
                            "X-Sync-Token": settings.CLOUD_SYNC_TOKEN,
                            "Content-Type": "application/json",
                        },
                        json=lote,
                    )

                if push_resp.status_code == 200:
                    now_dt = datetime.now(timezone.utc)
                    for r in pendientes:
                        r.estado = "APLICADO"
                        r.sincronizado_en = now_dt
                        r.ultimo_error = None
                    safe_commit(db)
                    _worker_status["ultima_sincronizacion"] = now_dt.isoformat()
                    # Recalcular pendientes
                    p_restantes = (
                        db.query(func.count(RegistroSync.id))
                        .filter(RegistroSync.estado == "PENDIENTE")
                        .scalar()
                        or 0
                    )
                    _worker_status["pendientes"] = int(p_restantes)
                else:
                    for r in pendientes:
                        r.reintentos += 1
                        r.ultimo_error = f"HTTP {push_resp.status_code}: {push_resp.text[:150]}"
                    safe_commit(db)
                    _worker_status["ultimo_error"] = f"Error al sincronizar lote: HTTP {push_resp.status_code}"
        except Exception as e:
            db.rollback()
            _worker_status["ultimo_error"] = f"Fallo al enviar lote: {str(e)}"
        finally:
            _worker_status["sincronizando"] = False
            db.close()

    return dict(_worker_status)


async def sync_background_loop():
    """Bucle infinito en segundo plano que corre durante el ciclo de vida del servidor."""
    if settings.MODO_CEREBRO == "NUBE" or not settings.CLOUD_SYNC_ENABLED:
        logger.info("Modo CEREBRO NUBE: Daemon saliente inactivo (servidor opera como receptor).")
        return

    # Espera 3 segundos iniciales para permitir que la BD y FastAPI terminen de iniciar
    await asyncio.sleep(3)
    while True:
        try:
            await ejecutar_ciclo_sync()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error inesperado en loop de sincronización: {e}", exc_info=True)

        intervalo = max(3, getattr(settings, "SYNC_INTERVAL_SECONDS", 10))
        await asyncio.sleep(intervalo)

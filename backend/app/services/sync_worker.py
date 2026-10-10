"""Worker de sincronización de la caja (modo LOCAL).

Corre dentro del backend y hace dos cosas, en este orden, en cada ciclo:
  1. BAJAR  los cambios hechos en el panel web y aplicarlos en la base local.
  2. SUBIR  a la nube todo lo pendiente de la cola local (`registro_sync`), incluido el estado
            en que quedó cada fila recién bajada, para que ambos lados terminen idénticos.

No espera al temporizador: cada vez que se confirma un cambio en la base de datos el worker
se despierta al instante, así el dueño ve la venta en la web segundos después de que ocurre.
Si no hay internet no pasa nada: la cola crece y se entrega al volver la conexión.
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import text

from app.config import settings
from app.core import replicacion
from app.database import engine

logger = logging.getLogger("sync_worker")

_worker_status: dict[str, Any] = {
    "online": True,
    "sincronizando": False,
    "pendientes": 0,
    "aplicadas": 0,
    "ultima_sincronizacion": None,
    "ultimo_error": None,
    "ultimo_chequeo": None,
}

LOTE = 200
MAX_LOTES_POR_CICLO = 25
# Tras N rechazos una operación se aparta (ERROR_SERVIDOR) para no reintentarla sin fin.
# Con la espera creciente entre intentos, eso equivale a unas 3 horas de insistencia.
MAX_REINTENTOS_OP = 20
ESPERA_MAXIMA_S = 600

_despertar: asyncio.Event | None = None
_loop: asyncio.AbstractEventLoop | None = None
_proximo_intento: dict[int, float] = {}   # id de operación -> instante en que se puede reintentar
_fallos_bajada: dict[int, int] = {}       # id de operación de la nube -> intentos fallidos


def get_worker_status() -> dict[str, Any]:
    return dict(_worker_status)


def despertar_worker() -> None:
    """Pide un ciclo inmediato. Seguro de llamar desde cualquier hilo."""
    if _loop is not None and _despertar is not None:
        try:
            _loop.call_soon_threadsafe(_despertar.set)
        except RuntimeError:
            pass


def _activo() -> bool:
    return settings.MODO_CEREBRO != "NUBE" and bool(settings.CLOUD_SYNC_ENABLED and settings.CLOUD_SYNC_URL)


def _cabeceras() -> dict[str, str]:
    return {"X-Sync-Token": settings.CLOUD_SYNC_TOKEN, "Content-Type": "application/json"}


# ------------------------------------------------------------------ acceso a la base (bloqueante)
def _config(conn, clave: str) -> str | None:
    return conn.execute(text("SELECT valor FROM configuracion WHERE clave = :c"), {"c": clave}).scalar()


def _guardar_config(conn, clave: str, valor: str, descripcion: str) -> None:
    conn.execute(
        text(
            "INSERT INTO configuracion (clave, valor, descripcion) VALUES (:c, :v, :d) "
            "ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor"
        ),
        {"c": clave, "v": valor, "d": descripcion},
    )


def _contar_pendientes() -> int:
    with engine.connect() as conn:
        return int(
            conn.execute(
                text("SELECT count(*) FROM registro_sync WHERE estado = 'PENDIENTE' AND origen = 'LOCAL'")
            ).scalar()
            or 0
        )


def _leer_lote() -> tuple[str, list[dict]]:
    from app.services.sync import instalacion_id

    ahora = time.time()
    en_espera = [i for i, t in _proximo_intento.items() if t > ahora]
    with engine.begin() as conn:
        inst = instalacion_id(conn)
        filas = conn.execute(
            text(
                "SELECT id, op_id, sucursal_id, tipo, entidad, entidad_id, entidad_uuid, payload "
                "FROM registro_sync WHERE estado = 'PENDIENTE' AND origen = 'LOCAL' "
                "AND tipo IN ('FILA', 'BORRAR') AND NOT (id = ANY(CAST(:espera AS integer[]))) ORDER BY id LIMIT :n"
            ),
            {"espera": en_espera, "n": LOTE},
        ).mappings().all()
    ops = [
        {
            "_id": f["id"],
            "op_id": f["op_id"],
            "sucursal_id": f["sucursal_id"] or "SUC-01",
            "dispositivo_id": inst,
            "tipo": f["tipo"],
            "entidad": f["entidad"],
            "entidad_id": f["entidad_id"],
            "entidad_uuid": f["entidad_uuid"],
            "payload": {**(f["payload"] or {}), "_seq": f["id"], "_inst": inst},
            "origen": "LOCAL",
        }
        for f in filas
    ]
    return inst, ops


def _asentar(ops: list[dict], resultados: dict[str, tuple[bool, str | None]]) -> tuple[int, str | None]:
    """Guarda en la cola local qué pasó con cada operación enviada."""
    aplicadas = 0
    primer_error = None
    ahora = time.time()
    with engine.begin() as conn:
        for op in ops:
            res = resultados.get(op["op_id"])
            if res is None:
                continue  # sin respuesta: se reintenta tal cual en el próximo ciclo
            if res[0]:
                conn.execute(
                    text(
                        "UPDATE registro_sync SET estado = 'APLICADO', sincronizado_en = now(), ultimo_error = NULL, "
                        "payload = jsonb_build_object('pk', payload->'pk') WHERE id = :i"
                    ),
                    {"i": op["_id"]},
                )
                _proximo_intento.pop(op["_id"], None)
                aplicadas += 1
            else:
                error = (res[1] or "Error en la nube")[:300]
                n = conn.execute(
                    text(
                        "UPDATE registro_sync SET reintentos = reintentos + 1, ultimo_error = :e, "
                        "estado = CASE WHEN reintentos + 1 >= :m THEN 'ERROR_SERVIDOR' ELSE estado END "
                        "WHERE id = :i RETURNING reintentos"
                    ),
                    {"e": error, "m": MAX_REINTENTOS_OP, "i": op["_id"]},
                ).scalar() or 1
                _proximo_intento[op["_id"]] = ahora + min(ESPERA_MAXIMA_S, 5 * (2 ** min(n, 10)))
                primer_error = primer_error or f"La nube rechazó {op['entidad']} {op['entidad_uuid']}: {error}"
                if n >= MAX_REINTENTOS_OP:
                    logger.error("Operación %s (%s %s) apartada tras %s rechazos", op["_id"], op["entidad"], op["entidad_uuid"], n)
    return aplicadas, primer_error


def _preparar_espejo(espejo_id: str) -> bool:
    """Si la nube es un espejo nuevo (o recién reiniciado), se le envía la base completa."""
    with engine.begin() as conn:
        if _config(conn, "sync_espejo_id") == espejo_id:
            return False
        # Lo pendiente de versiones anteriores queda reemplazado por la copia completa
        conn.execute(
            text(
                "UPDATE registro_sync SET estado = 'APLICADO', sincronizado_en = now(), "
                "resolucion_nota = 'Reemplazada por la copia completa enviada al espejo' "
                "WHERE origen = 'LOCAL' AND estado <> 'APLICADO'"
            )
        )
        total = replicacion.encolar_snapshot_completo(conn)
        _guardar_config(conn, "sync_espejo_id", espejo_id, "Espejo en la nube al que está vinculada esta caja")
        _guardar_config(conn, "sync_cursor_nube", "0", "Última operación de la nube aplicada en esta caja")
    _proximo_intento.clear()
    _fallos_bajada.clear()
    logger.info("Espejo nuevo detectado (%s): %s filas encoladas para copia completa", espejo_id, total)
    return True


def _aplicar_cambio_nube(op: dict) -> str:
    """Aplica en la base local UNA operación del panel web y avanza el cursor. Devuelve la tabla."""
    with engine.begin() as conn:
        devolver = replicacion.aplicar_operacion(
            conn, op["tipo"], op["entidad"], op["payload"], origen_op="NUBE"
        )
        for tabla, pk in devolver:
            replicacion.encolar_fila(conn, tabla, pk)
        _guardar_config(conn, "sync_cursor_nube", str(op["id"]), "Última operación de la nube aplicada en esta caja")
    return op["entidad"]


def _saltar_cambio_nube(op: dict, error: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO registro_sync (op_id, sucursal_id, dispositivo_id, tipo, entidad, entidad_id, "
                "entidad_uuid, payload, origen, estado, reintentos, ultimo_error) VALUES (:o, :s, 'NUBE', :t, :e, "
                ":ei, :eu, CAST(:p AS jsonb), 'NUBE', 'CONFLICTO', :r, :err) ON CONFLICT (op_id) DO NOTHING"
            ),
            {
                "o": op["op_id"], "s": op.get("sucursal_id") or "SUC-01", "t": op["tipo"], "e": op["entidad"],
                "ei": op.get("entidad_id"), "eu": op.get("entidad_uuid"), "p": json.dumps(op["payload"], default=str),
                "r": MAX_REINTENTOS_OP, "err": error[:300],
            },
        )
        _guardar_config(conn, "sync_cursor_nube", str(op["id"]), "Última operación de la nube aplicada en esta caja")


def _limpiar_cola_antigua() -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM registro_sync WHERE estado = 'APLICADO' AND sincronizado_en < now() - interval '15 days'")
        )


# ------------------------------------------------------------------ ciclo
def _leer_resultados(resp: httpx.Response, ops: list[dict]) -> dict[str, tuple[bool, str | None]]:
    resultados: dict[str, tuple[bool, str | None]] = {}
    try:
        for r in resp.json().get("resultados") or []:
            resultados[r["op_id"]] = (r.get("estado") != "ERROR", r.get("error"))
    except Exception:
        pass
    return resultados


async def _subir(client: httpx.AsyncClient, cloud_url: str) -> None:
    for _ in range(MAX_LOTES_POR_CICLO):
        inst, ops = await asyncio.to_thread(_leer_lote)
        if not ops:
            return
        _worker_status["sincronizando"] = True
        cuerpo = {"dispositivo_id": inst, "operaciones": [{k: v for k, v in o.items() if k != "_id"} for o in ops]}
        resp = await client.post(f"{cloud_url}/sync/push", headers=_cabeceras(), content=json.dumps(cuerpo, default=str))
        if resp.status_code not in (200, 207):
            raise RuntimeError(f"La nube respondió HTTP {resp.status_code} al subir: {resp.text[:200]}")
        aplicadas, error = await asyncio.to_thread(_asentar, ops, _leer_resultados(resp, ops))
        if aplicadas:
            _worker_status["ultima_sincronizacion"] = datetime.now(timezone.utc).isoformat()
            _worker_status["aplicadas"] = _worker_status.get("aplicadas", 0) + aplicadas
        if error:
            _worker_status["ultimo_error"] = error
        if aplicadas == 0:
            return  # nada avanzó en este lote: no insistir hasta el próximo ciclo


async def _bajar(client: httpx.AsyncClient, cloud_url: str) -> int:
    """Descarga y aplica los cambios del panel web. Devuelve cuántos aplicó."""
    from app.services.sync import TABLAS_CATALOGO
    from app.services.websocket import ws_manager

    def _cursor() -> int:
        with engine.connect() as conn:
            return int(_config(conn, "sync_cursor_nube") or 0)

    total = 0
    tablas: set[str] = set()
    for _ in range(MAX_LOTES_POR_CICLO):
        cursor = await asyncio.to_thread(_cursor)
        resp = await client.get(
            f"{cloud_url}/sync/cambios", headers=_cabeceras(), params={"despues_de": cursor, "limite": LOTE}
        )
        if resp.status_code != 200:
            raise RuntimeError(f"La nube respondió HTTP {resp.status_code} al bajar cambios: {resp.text[:200]}")
        datos = resp.json()
        if await asyncio.to_thread(_preparar_espejo, datos.get("espejo_id") or ""):
            return total  # espejo nuevo: primero se sube la copia completa
        ops = datos.get("operaciones") or []
        if not ops:
            break

        detenido = False
        for op in ops:
            try:
                tablas.add(await asyncio.to_thread(_aplicar_cambio_nube, op))
                _fallos_bajada.pop(op["id"], None)
                total += 1
            except Exception as e:
                error = (str(e).splitlines() or [""])[0][:300] or type(e).__name__
                n = _fallos_bajada.get(op["id"], 0) + 1
                _fallos_bajada[op["id"]] = n
                _worker_status["ultimo_error"] = f"No se pudo aplicar un cambio del panel web ({op['entidad']}): {error}"
                if n >= MAX_REINTENTOS_OP:
                    logger.error("Cambio de la nube %s (%s) descartado tras %s intentos: %s", op["id"], op["entidad"], n, error)
                    await asyncio.to_thread(_saltar_cambio_nube, op, error)
                    continue
                detenido = True  # se reintenta en el próximo ciclo, respetando el orden
                break
        if detenido or len(ops) < LOTE:
            break

    if total:
        cursor = await asyncio.to_thread(_cursor)
        try:
            await client.post(f"{cloud_url}/sync/confirmar", headers=_cabeceras(), json={"hasta_id": cursor})
        except Exception:
            pass
        await ws_manager.broadcast({"evento": "datos_sincronizados", "data": {"origen": "NUBE", "tablas": sorted(tablas)}})
        if tablas & TABLAS_CATALOGO:
            await ws_manager.broadcast({"evento": "catalogo_actualizado", "data": {"tipo": "sincronizacion_nube"}})
    return total


async def ejecutar_ciclo_sync() -> dict[str, Any]:
    """Un ciclo completo: subir, bajar y volver a subir lo que la bajada haya generado."""
    if not _activo():
        _worker_status["online"] = True
        return dict(_worker_status)

    _worker_status["ultimo_chequeo"] = datetime.now(timezone.utc).isoformat()
    cloud_url = settings.CLOUD_SYNC_URL.rstrip("/")
    try:
        # Tiempos amplios: el plan gratuito de Render tarda en despertar tras estar inactivo
        async with httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=30.0)) as client:
            salud = await client.get(f"{cloud_url}/sync/health")
            if salud.status_code != 200:
                raise RuntimeError(f"La nube respondió HTTP {salud.status_code}")
            _worker_status["online"] = True
            _worker_status["ultimo_error"] = None
            # Primero bajar: detecta un espejo nuevo antes de subir nada, y lo que la bajada
            # deja en la cola (el estado resultante de cada fila) sale en la subida siguiente.
            await _bajar(client, cloud_url)
            await _subir(client, cloud_url)
    except (httpx.HTTPError, OSError):
        _worker_status["online"] = False
        _worker_status["ultimo_error"] = "Sin conexión a la nube (operando en modo local autónomo)"
    except Exception as e:
        _worker_status["ultimo_error"] = (str(e) or type(e).__name__)[:300]
        logger.warning("Ciclo de sincronización con error: %s", _worker_status["ultimo_error"])
    finally:
        _worker_status["sincronizando"] = False
        try:
            _worker_status["pendientes"] = await asyncio.to_thread(_contar_pendientes)
        except Exception:
            pass
    return dict(_worker_status)


async def sync_background_loop() -> None:
    """Bucle del worker: un ciclo cada SYNC_INTERVAL_SECONDS o en cuanto haya algo nuevo que subir."""
    global _despertar, _loop
    if not _activo():
        logger.info("Worker de sincronización inactivo (modo NUBE o sin espejo configurado).")
        return

    _loop = asyncio.get_running_loop()
    _despertar = asyncio.Event()
    await asyncio.sleep(3)  # deja terminar el arranque de la base y de FastAPI
    ultima_limpieza = 0.0
    while True:
        try:
            _despertar.clear()
            await ejecutar_ciclo_sync()
            if time.time() - ultima_limpieza > 3600:
                ultima_limpieza = time.time()
                await asyncio.to_thread(_limpiar_cola_antigua)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error inesperado en el worker de sincronización: %s", e, exc_info=True)

        intervalo = max(3, int(getattr(settings, "SYNC_INTERVAL_SECONDS", 5) or 5))
        if not _worker_status.get("online", True):
            intervalo = max(intervalo, 15)  # sin internet no vale la pena insistir cada pocos segundos
        try:
            await asyncio.wait_for(_despertar.wait(), timeout=intervalo)
            await asyncio.sleep(0.3)  # agrupa los cambios de una misma acción en un solo envío
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            break

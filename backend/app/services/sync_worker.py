import asyncio
from decimal import Decimal
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import func

from app.config import settings
from app.database import SessionLocal, safe_commit
from app.models import Producto, Usuario
from app.models.configuracion import Configuracion
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


# Tras N rechazos de la nube, una operación se aísla (ERROR_SERVIDOR) para no bloquear a las demás.
MAX_REINTENTOS_OP = 20


async def _post_push(client: httpx.AsyncClient, cloud_url: str, operaciones: list[dict]) -> httpx.Response:
    return await client.post(
        f"{cloud_url}/sync/push",
        headers={"X-Sync-Token": settings.CLOUD_SYNC_TOKEN, "Content-Type": "application/json"},
        json={"dispositivo_id": settings.SUCURSAL_ID, "operaciones": operaciones},
    )


def _leer_resultados(resp: httpx.Response, operaciones: list[dict], destino: dict[str, tuple[bool, str | None]]) -> None:
    """Traduce la respuesta del push a {op_id: (ok, error)}.

    La nube nueva responde 200/207 con `resultados` por operación. Una nube antigua responde 200 sin
    `resultados`: en ese caso 200 significa que todo el lote quedó aplicado.
    """
    try:
        cuerpo = resp.json()
    except Exception:
        cuerpo = {}
    por_op = {x.get("op_id"): x for x in (cuerpo.get("resultados") or [])}
    for op in operaciones:
        x = por_op.get(op["op_id"])
        if x is None:
            ok = resp.status_code == 200
            destino[op["op_id"]] = (ok, None if ok else "La nube no informó el resultado de la operación")
        else:
            ok = x.get("estado") in ("APLICADO", "DUPLICADO", "CONFLICTO")
            destino[op["op_id"]] = (ok, None if ok else (x.get("error") or "Error desconocido en la nube"))


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
        pendientes_data = []
        pendientes_ids = []
        try:
            pendientes = (
                db.query(RegistroSync)
                .filter(RegistroSync.estado == "PENDIENTE")
                .order_by(RegistroSync.id.asc())
                .limit(50)
                .all()
            )
            if pendientes:
                pendientes_ids = [r.id for r in pendientes]
                pendientes_data = [
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
                ]
        finally:
            db.close()

        if pendientes_data:
            _worker_status["sincronizando"] = True
            resultados: dict[str, tuple[bool, str | None]] = {}
            error_red = None
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    push_resp = await _post_push(client, cloud_url, pendientes_data)
                    if push_resp.status_code in (200, 207):
                        _leer_resultados(push_resp, pendientes_data, resultados)
                    else:
                        # Lote rechazado completo (nube con versión vieja, 422 por una sola operación,
                        # etc.). Se prueba operación por operación para que UNA mala no bloquee la cola.
                        logger.warning(
                            "Lote rechazado (HTTP %s); reintentando operación por operación", push_resp.status_code
                        )
                        for op in pendientes_data:
                            r1 = await _post_push(client, cloud_url, [op])
                            if r1.status_code in (200, 207):
                                _leer_resultados(r1, [op], resultados)
                            else:
                                resultados[op["op_id"]] = (False, f"HTTP {r1.status_code}: {r1.text[:150]}")
            except Exception as e:
                error_red = str(e) or type(e).__name__

            # Abrir nueva sesión para asentar el resultado de cada operación
            db = SessionLocal()
            try:
                records = db.query(RegistroSync).filter(RegistroSync.id.in_(pendientes_ids)).all()
                now_dt = datetime.now(timezone.utc)
                aplicadas_ok = 0
                primer_error = None
                for r in records:
                    res = resultados.get(r.op_id)
                    if res is None:
                        # sin respuesta de la nube (caída de red): se reintenta en el próximo ciclo
                        r.reintentos += 1
                        r.ultimo_error = f"Fallo de red al enviar lote: {error_red}"
                        primer_error = primer_error or f"Fallo al enviar lote: {error_red}"
                    elif res[0]:
                        r.estado = "APLICADO"
                        r.sincronizado_en = now_dt
                        r.ultimo_error = None
                        aplicadas_ok += 1
                    else:
                        r.reintentos += 1
                        r.ultimo_error = (res[1] or "Error en la nube")[:300]
                        primer_error = primer_error or f"La nube rechazó {r.tipo} #{r.entidad_id}: {r.ultimo_error}"
                        if r.reintentos >= MAX_REINTENTOS_OP:
                            r.estado = "ERROR_SERVIDOR"
                            logger.error(
                                "Operación sync id=%s (%s) aislada tras %s rechazos de la nube.",
                                r.id, r.tipo, r.reintentos,
                            )
                safe_commit(db)
                if aplicadas_ok:
                    _worker_status["ultima_sincronizacion"] = now_dt.isoformat()
                _worker_status["ultimo_error"] = primer_error
                p_restantes = (
                    db.query(func.count(RegistroSync.id))
                    .filter(RegistroSync.estado == "PENDIENTE")
                    .scalar()
                    or 0
                )
                _worker_status["pendientes"] = int(p_restantes)
            except Exception as e:
                db.rollback()
                _worker_status["ultimo_error"] = f"Fallo al asentar lote: {str(e)}"
            finally:
                _worker_status["sincronizando"] = False
                db.close()

    return dict(_worker_status)


_cached_cloud_token: str | None = None
_cached_cloud_token_exp: float = 0


async def _obtener_token_nube(client: httpx.AsyncClient, cloud_url: str) -> str | None:
    global _cached_cloud_token, _cached_cloud_token_exp
    if _cached_cloud_token and time.time() < _cached_cloud_token_exp:
        return _cached_cloud_token

    credenciales = []
    if settings.CLOUD_SYNC_USER and settings.CLOUD_SYNC_PASSWORD:
        credenciales.append((settings.CLOUD_SYNC_USER, settings.CLOUD_SYNC_PASSWORD))
    credenciales += [
        ("omarvelandia", "omarvelandia123"),
        ("admin", "admin123"),
    ]
    for usr, pwd in credenciales:
        try:
            resp = await client.post(
                f"{cloud_url}/api/auth/login",
                data={"username": usr, "password": pwd},
                timeout=6.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                _cached_cloud_token = data.get("access_token")
                _cached_cloud_token_exp = time.time() + 18000  # 5 horas
                return _cached_cloud_token
        except Exception:
            continue
    return None


async def replicar_admin_a_nube(metodo: str, endpoint: str, data: dict | list | None = None) -> None:
    """Si estamos en modo LOCAL con sincronización activa, replica inmediatamente
    el cambio administrativo (producto, ingrediente, receta, etc.) en Render.
    """
    if settings.MODO_CEREBRO == "NUBE" or not settings.CLOUD_SYNC_ENABLED or not settings.CLOUD_SYNC_URL:
        return

    cloud_url = settings.CLOUD_SYNC_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            token = await _obtener_token_nube(client, cloud_url)
            if not token:
                return
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            url = f"{cloud_url}/api{endpoint}"
            m = metodo.upper()
            if m == "POST":
                await client.post(url, json=data, headers=headers)
            elif m == "PUT":
                await client.put(url, json=data, headers=headers)
            elif m == "DELETE":
                await client.delete(url, headers=headers)
            logger.info(f"Replicación administrativa a la nube exitosa: {m} {endpoint}")
    except Exception as e:
        logger.warning(f"Aviso replicando cambio a la nube ({endpoint}): {e}")


async def ejecutar_ciclo_pull() -> dict[str, Any]:
    """Descarga e integra en la BD local cualquier cambio realizado desde la Web/Nube.
    
    Regla del Documento Maestro:
    - Autoridad: Lo que configura el admin en la nube (catálogo, precios, usuarios, configuraciones)
      baja automáticamente a las terminales locales.
    """
    if settings.MODO_CEREBRO == "NUBE" or not settings.CLOUD_SYNC_ENABLED or not settings.CLOUD_SYNC_URL:
        return {"productos": 0, "usuarios": 0, "configuracion": 0}

    cloud_url = settings.CLOUD_SYNC_URL.rstrip("/")
    actualizaciones = {"productos": 0, "usuarios": 0, "configuracion": 0}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token = await _obtener_token_nube(client, cloud_url)
            if not token:
                return actualizaciones

            auth_headers = {"Authorization": f"Bearer {token}"}

            # 1. Sincronizar Catálogo de Productos y Precios
            try:
                p_resp = await client.get(f"{cloud_url}/api/productos", headers=auth_headers)
                if p_resp.status_code == 200:
                    cloud_prods = p_resp.json()
                    db = SessionLocal()
                    try:
                        cambio_catalogo = False
                        for cp in cloud_prods:
                            pid = cp.get("id")
                            lp = db.get(Producto, pid)
                            cloud_precio = Decimal(str(cp.get("precio", 0)))
                            if lp:
                                modificado = False
                                if abs(lp.precio - cloud_precio) > Decimal("0.01"):
                                    lp.precio = cloud_precio
                                    modificado = True
                                if lp.nombre != cp.get("nombre"):
                                    lp.nombre = cp.get("nombre")
                                    modificado = True
                                if lp.activo != cp.get("activo", True):
                                    lp.activo = cp.get("activo", True)
                                    modificado = True
                                if lp.manual_disponible != cp.get("manual_disponible"):
                                    lp.manual_disponible = cp.get("manual_disponible")
                                    modificado = True
                                if modificado:
                                    actualizaciones["productos"] += 1
                                    cambio_catalogo = True
                            else:
                                nuevo_p = Producto(
                                    id=pid,
                                    categoria_id=cp.get("categoria_id", 1),
                                    nombre=cp.get("nombre", ""),
                                    descripcion=cp.get("descripcion", ""),
                                    precio=cloud_precio,
                                    iva_incluido=cp.get("iva_incluido", True),
                                    activo=cp.get("activo", True),
                                    manual_disponible=cp.get("manual_disponible"),
                                    permite_adiciones=cp.get("permite_adiciones", True),
                                )
                                db.add(nuevo_p)
                                actualizaciones["productos"] += 1
                                cambio_catalogo = True

                        if cambio_catalogo:
                            safe_commit(db)
                            from app.services.websocket import ws_manager
                            await ws_manager.broadcast({
                                "evento": "catalogo_actualizado",
                                "data": {"tipo": "sincronizacion_nube", "actualizados": actualizaciones["productos"]}
                            })
                            logger.info(f"PULL: Catálogo local actualizado con {actualizaciones['productos']} cambio(s) desde la nube.")
                    finally:
                        db.close()
            except Exception as e:
                logger.warning(f"Aviso al descargar productos de la nube: {e}")

            # 2. Sincronizar Usuarios creados o modificados en la Web
            try:
                u_resp = await client.get(f"{cloud_url}/api/admin/usuarios", headers=auth_headers)
                if u_resp.status_code == 200:
                    cloud_users = u_resp.json()
                    db = SessionLocal()
                    try:
                        hubo_cambio_u = False
                        for cu in cloud_users:
                            uid = cu.get("id")
                            lu = db.get(Usuario, uid)
                            if not lu:
                                nuevo_u = Usuario(
                                    id=uid,
                                    nombre=cu.get("nombre", ""),
                                    usuario=cu.get("usuario", ""),
                                    rol_id=cu.get("rol_id", 2),
                                    password_hash=cu.get("password_hash") or "$2b$12$UR9zR9cwj5ffRV9B9oJdteyUkDG5MKTTuANe8aYzqZ1hv0VO70cc.",
                                    activo=cu.get("activo", True),
                                    fijado=cu.get("fijado", False),
                                    es_demo=cu.get("es_demo", False),
                                )
                                db.add(nuevo_u)
                                actualizaciones["usuarios"] += 1
                                hubo_cambio_u = True
                            else:
                                mod_u = False
                                if lu.activo != cu.get("activo", True):
                                    lu.activo = cu.get("activo", True)
                                    mod_u = True
                                if lu.rol_id != cu.get("rol_id", lu.rol_id):
                                    lu.rol_id = cu.get("rol_id", lu.rol_id)
                                    mod_u = True
                                if lu.fijado != cu.get("fijado", lu.fijado):
                                    lu.fijado = cu.get("fijado", lu.fijado)
                                    mod_u = True
                                if mod_u:
                                    actualizaciones["usuarios"] += 1
                                    hubo_cambio_u = True
                        if hubo_cambio_u:
                            safe_commit(db)
                            logger.info(f"PULL: Usuarios locales sincronizados con {actualizaciones['usuarios']} cambio(s) desde la nube.")
                    finally:
                        db.close()
            except Exception as e:
                logger.warning(f"Aviso al sincronizar usuarios de la nube: {e}")

            # 3. Sincronizar Configuración Global
            try:
                c_resp = await client.get(f"{cloud_url}/api/admin/configuracion", headers=auth_headers)
                if c_resp.status_code == 200:
                    cloud_configs = c_resp.json()
                    db = SessionLocal()
                    try:
                        hubo_cambio_cfg = False
                        for cfg in cloud_configs:
                            k = cfg.get("clave")
                            v = cfg.get("valor")
                            if k and v is not None:
                                local_cfg = db.get(Configuracion, k)
                                if local_cfg and local_cfg.valor != str(v):
                                    local_cfg.valor = str(v)
                                    actualizaciones["configuracion"] += 1
                                    hubo_cambio_cfg = True
                                elif not local_cfg:
                                    nuevo_cfg = Configuracion(clave=k, valor=str(v), descripcion=cfg.get("descripcion"))
                                    db.add(nuevo_cfg)
                                    actualizaciones["configuracion"] += 1
                                    hubo_cambio_cfg = True
                        if hubo_cambio_cfg:
                            safe_commit(db)
                    finally:
                        db.close()
            except Exception as e:
                logger.warning(f"Aviso al sincronizar configuración de la nube: {e}")

    except Exception as e:
        logger.warning(f"Fallo en ciclo de descarga (pull) desde la nube: {e}")

    return actualizaciones


async def sync_background_loop():
    """Bucle infinito en segundo plano que corre durante el ciclo de vida del servidor."""
    if settings.MODO_CEREBRO == "NUBE" or not settings.CLOUD_SYNC_ENABLED:
        logger.info("Modo CEREBRO NUBE: Daemon saliente inactivo (servidor opera como receptor).")
        return

    # Espera 3 segundos iniciales para permitir que la BD y FastAPI terminen de iniciar
    await asyncio.sleep(3)
    ciclo_pull_contador = 0
    while True:
        try:
            await ejecutar_ciclo_sync()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error inesperado en loop de sincronización (push): {e}", exc_info=True)

        # Cada 2 ciclos (~20 segundos), verificar y descargar cambios hechos en la Web (PULL)
        ciclo_pull_contador += 1
        if ciclo_pull_contador >= 2:
            ciclo_pull_contador = 0
            try:
                await ejecutar_ciclo_pull()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error inesperado en loop de sincronización (pull): {e}", exc_info=True)

        intervalo = max(3, getattr(settings, "SYNC_INTERVAL_SECONDS", 10))
        await asyncio.sleep(intervalo)

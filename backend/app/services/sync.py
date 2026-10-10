"""Servicio de sincronización: recepción de operaciones, estado y utilidades del espejo.

La réplica en sí (captura y aplicación de filas) vive en `app.core.replicacion`.
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.config import settings
from app.core import replicacion
from app.database import Base, safe_commit
from app.models import RegistroSync, Usuario
from app.schemas.sync import (
    SyncEstadoOut,
    SyncOpIn,
    SyncOpOut,
    SyncOpResultado,
    SyncPushIn,
    SyncPushOut,
)

logger = logging.getLogger("sync")

# Tablas cuyo cambio obliga a los dispositivos a recargar el catálogo
TABLAS_CATALOGO = {
    "tipo_categoria", "categoria", "producto", "componente_combo", "detalle_receta",
    "categoria_insumo", "ingrediente", "configuracion",
}


def encolar_sync(*_args, **_kwargs) -> None:
    """Obsoleta. La réplica por filas (`app.core.replicacion`) registra sola cada cambio
    confirmado, con todos sus campos. Se conserva la función para no romper llamadas antiguas."""
    return None


def instalacion_id(conn) -> str:
    """Identificador único de ESTA base de datos. Permite a la nube distinguir la numeración
    de operaciones de una instalación nueva frente a la de una anterior."""
    valor = conn.execute(text("SELECT valor FROM configuracion WHERE clave = 'sync_instalacion_id'")).scalar()
    if valor:
        return valor
    valor = str(uuid.uuid4())
    conn.execute(
        text(
            "INSERT INTO configuracion (clave, valor, descripcion) VALUES "
            "('sync_instalacion_id', :v, 'Identificador de esta instalación para la sincronización') "
            "ON CONFLICT (clave) DO NOTHING"
        ),
        {"v": valor},
    )
    return conn.execute(text("SELECT valor FROM configuracion WHERE clave = 'sync_instalacion_id'")).scalar()


def espejo_id(conn) -> str:
    """Identificador del espejo (nube). Cambia cada vez que el espejo se reinicia; la caja lo
    compara con el que tiene guardado para saber si debe enviar la base completa de nuevo."""
    valor = conn.execute(text("SELECT valor FROM configuracion WHERE clave = 'sync_espejo_id'")).scalar()
    if valor:
        return valor
    conn.execute(
        text(
            "INSERT INTO configuracion (clave, valor, descripcion) VALUES "
            "('sync_espejo_id', :v, 'Identificador de este espejo en la nube') ON CONFLICT (clave) DO NOTHING"
        ),
        {"v": str(uuid.uuid4())},
    )
    return conn.execute(text("SELECT valor FROM configuracion WHERE clave = 'sync_espejo_id'")).scalar()


def _archivar_datos_de_negocio(conn) -> str | None:
    """Antes de vaciar el espejo, guarda una copia de todo lo que tenga en el esquema `archivo`.

    Regla del negocio: nada se borra. Recetas, precios, ventas e insumos que estuvieran en la
    nube quedan consultables (tablas `archivo."<tabla>__<fecha>"`) aunque el espejo se reemplace.
    Devuelve el sufijo usado, o None si no había nada que guardar.
    """
    sufijo = conn.execute(text("SELECT to_char(now() AT TIME ZONE 'UTC', 'YYYYMMDD_HH24MISS')")).scalar()
    guardadas = 0
    for tabla in Base.metadata.sorted_tables:
        if not conn.execute(text(f'SELECT EXISTS (SELECT 1 FROM "{tabla.name}")')).scalar():
            continue
        if guardadas == 0:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS archivo"))
        conn.execute(text(f'CREATE TABLE archivo."{tabla.name}__{sufijo}" AS SELECT * FROM "{tabla.name}"'))
        guardadas += 1
    if not guardadas:
        return None
    # El archivo no debe quedar expuesto por la API pública de Supabase
    conn.execute(
        text(
            """
            DO $$
            DECLARE r text;
            BEGIN
                FOREACH r IN ARRAY ARRAY['anon', 'authenticated'] LOOP
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
                        EXECUTE format('REVOKE ALL ON SCHEMA archivo FROM %I', r);
                        EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA archivo FROM %I', r);
                    END IF;
                END LOOP;
            END $$;
            """
        )
    )
    logger.warning("Datos del espejo archivados en el esquema 'archivo' con sufijo %s (%s tablas)", sufijo, guardadas)
    return sufijo


def _vaciar_datos_de_negocio(conn) -> int:
    """Deja el espejo sin datos de negocio, conservando sus banderas internas.
    Siempre archiva primero lo que hubiera: vaciar el espejo nunca destruye información."""
    _archivar_datos_de_negocio(conn)
    tablas = [t.name for t in Base.metadata.sorted_tables if t.name != "configuracion"]
    conn.execute(text("TRUNCATE TABLE " + ", ".join(f'"{t}"' for t in tablas) + " RESTART IDENTITY CASCADE"))
    filtro = " AND ".join(f"clave NOT LIKE '{p}%'" for p in replicacion.PREFIJOS_CONFIG_INTERNOS)
    conn.execute(text(f"DELETE FROM configuracion WHERE {filtro}"))
    replicacion.reservar_rango_nube(conn)
    return len(tablas)


def verificar_vinculo(conn, instalacion: str) -> None:
    """Un espejo recibe datos de UNA sola caja. La primera que sube queda vinculada; cualquier
    otra (por ejemplo un PC de desarrollo apuntando por error a producción) es rechazada, porque
    mezclar dos bases con la misma numeración corrompe el espejo.

    Al vincularse por primera vez el espejo se vacía: lo que tuviera (datos de prueba, restos
    de una versión anterior) no proviene de esa caja y chocaría con su copia completa."""
    actual = conn.execute(
        text("SELECT valor FROM configuracion WHERE clave = 'sync_instalacion_vinculada'")
    ).scalar()
    if not actual:
        _vaciar_datos_de_negocio(conn)
        logger.warning("Espejo vinculado a la caja %s: datos anteriores eliminados para recibir su copia", instalacion)
        conn.execute(
            text(
                "INSERT INTO configuracion (clave, valor, descripcion) VALUES "
                "('sync_instalacion_vinculada', :v, 'Caja autorizada a subir datos a este espejo') "
                "ON CONFLICT (clave) DO NOTHING"
            ),
            {"v": instalacion},
        )
        return
    if actual != instalacion:
        raise PermissionError(
            "Este espejo ya está vinculado a otra caja. Para vincular una nueva hay que reiniciar el espejo."
        )


# ------------------------------------------------------------------ recepción (nube)
def _es_obsoleta(db: Session, op: SyncOpIn) -> bool:
    """True si ya se aplicó un estado MÁS NUEVO de la misma fila enviado por la misma instalación.
    Protege contra reintentos tardíos que pisarían un dato reciente con uno viejo."""
    seq = op.payload.get("_seq")
    inst = op.payload.get("_inst")
    if seq is None or not inst:
        return False
    fila = db.execute(
        text(
            "SELECT 1 FROM registro_sync WHERE entidad = :e AND entidad_uuid = :u AND origen = 'LOCAL' "
            "AND estado = 'APLICADO' AND payload->>'_inst' = :i AND (payload->>'_seq')::bigint > :s LIMIT 1"
        ),
        {"e": op.entidad, "u": op.entidad_uuid or replicacion.pk_texto(op.payload.get("pk") or {}), "i": inst, "s": int(seq)},
    ).first()
    return fila is not None


def procesar_push(db: Session, data: SyncPushIn) -> tuple[SyncPushOut, set[str]]:
    """Aplica un lote de operaciones enviadas por la caja. Devuelve el resultado y las tablas tocadas.

    - Idempotente: una operación ya recibida (mismo `op_id`) se responde como DUPLICADO.
    - Cada operación va en su propio SAVEPOINT: si una falla, las demás se aplican igual.
    """
    procesadas = duplicadas = errores = 0
    resultados: list[SyncOpResultado] = []
    tablas: set[str] = set()

    # Solo una caja con el motor de réplica por filas puede vincularse al espejo. Un envío de una
    # versión anterior (operaciones "heredadas") se registra sin aplicar y NO vincula ni vacía nada.
    es_replica = any(
        op.tipo in replicacion.TIPOS_REPLICA and op.payload.get("_inst") == data.dispositivo_id
        for op in data.operaciones
    )
    if es_replica:
        verificar_vinculo(db.connection(), data.dispositivo_id)
    elif any(op.tipo in replicacion.TIPOS_REPLICA for op in data.operaciones):
        raise PermissionError("Lote de réplica sin identificador de instalación válido")

    # Lo que se aplica aquí viene de la caja: no debe registrarse como cambio propio de la nube.
    db.info["_replicacion_omitir"] = True
    try:
        for op in data.operaciones:
            if db.query(RegistroSync.id).filter(RegistroSync.op_id == op.op_id).first():
                duplicadas += 1
                resultados.append(SyncOpResultado(op_id=op.op_id, estado="DUPLICADO"))
                continue

            nota = None
            try:
                with db.begin_nested():
                    pk = op.payload.get("pk") or {}
                    if op.tipo in replicacion.TIPOS_REPLICA:
                        if _es_obsoleta(db, op):
                            nota = "Omitida: ya se aplicó un estado más reciente de esta fila"
                        else:
                            replicacion.aplicar_operacion(
                                db.connection(), op.tipo, op.entidad, op.payload, origen_op="LOCAL"
                            )
                            tablas.add(op.entidad)
                        # En la nube no se guarda la fila completa otra vez: solo su rastro.
                        guardado = {"pk": pk, "_seq": op.payload.get("_seq"), "_inst": op.payload.get("_inst")}
                    else:
                        nota = "Tipo de operación de una versión anterior: registrada sin aplicar"
                        guardado = {"tipo_heredado": op.tipo}

                    db.add(
                        RegistroSync(
                            op_id=op.op_id,
                            sucursal_id=op.sucursal_id,
                            dispositivo_id=op.dispositivo_id,
                            tipo=op.tipo,
                            entidad=op.entidad,
                            entidad_id=op.entidad_id,
                            entidad_uuid=op.entidad_uuid or replicacion.pk_texto(pk),
                            payload=guardado,
                            origen="LOCAL",
                            estado="APLICADO",
                            resolucion_nota=nota,
                            sincronizado_en=func.now(),
                        )
                    )
                    db.flush()
            except Exception as e:
                errores += 1
                detalle = (str(e).splitlines() or [""])[0][:300] or type(e).__name__
                logger.warning("Operación %s %s rechazada: %s", op.tipo, op.entidad, detalle)
                resultados.append(SyncOpResultado(op_id=op.op_id, estado="ERROR", error=detalle))
                continue

            procesadas += 1
            resultados.append(SyncOpResultado(op_id=op.op_id, estado="APLICADO"))

        safe_commit(db)
    finally:
        db.info.pop("_replicacion_omitir", None)

    return (
        SyncPushOut(
            procesadas=procesadas, duplicadas=duplicadas, conflictos=0, errores=errores,
            operaciones=[], resultados=resultados,
        ),
        tablas,
    )


# ------------------------------------------------------------------ bajada (nube -> caja)
def obtener_cambios_nube(db: Session, despues_de: int, limite: int = 200) -> list[SyncOpOut]:
    """Cambios hechos en el panel web que la caja todavía no ha descargado, en orden."""
    ops = (
        db.query(RegistroSync)
        .filter(
            RegistroSync.origen == "NUBE",
            RegistroSync.tipo.in_(replicacion.TIPOS_REPLICA),
            RegistroSync.id > despues_de,
        )
        .order_by(RegistroSync.id.asc())
        .limit(limite)
        .all()
    )
    return [SyncOpOut.model_validate(o) for o in ops]


def confirmar_bajada(db: Session, hasta_id: int) -> int:
    """La caja avisa hasta qué operación de la nube ya aplicó."""
    n = db.execute(
        text(
            "UPDATE registro_sync SET estado = 'APLICADO', sincronizado_en = now() "
            "WHERE origen = 'NUBE' AND estado = 'PENDIENTE' AND id <= :h"
        ),
        {"h": hasta_id},
    ).rowcount
    # Limpieza: el rastro de operaciones viejas ya aplicadas no hace falta conservarlo
    db.execute(
        text("DELETE FROM registro_sync WHERE estado = 'APLICADO' AND sincronizado_en < now() - interval '30 days'")
    )
    db.commit()
    return n or 0


def obtener_pull(
    db: Session,
    since: datetime | None = None,
    origen_filtro: str | None = None,
    limit: int = 100,
) -> list[SyncOpOut]:
    """Consulta el registro de operaciones (diagnóstico)."""
    q = db.query(RegistroSync).order_by(RegistroSync.creado_en.asc())
    if since:
        q = q.filter(RegistroSync.creado_en > since)
    if origen_filtro:
        q = q.filter(RegistroSync.origen == origen_filtro)
    return [SyncOpOut.model_validate(o) for o in q.limit(limit).all()]


# ------------------------------------------------------------------ reinicio del espejo
def reiniciar_espejo(db: Session) -> dict:
    """SOLO NUBE. Vacía los datos de negocio del espejo para reconstruirlo desde la caja.

    Se usa una vez al instalar (o reinstalar) la caja: garantiza que la nube quede idéntica al
    restaurante, sin restos de pruebas ni identificadores que choquen.
    """
    if settings.MODO_CEREBRO != "NUBE":
        raise ValueError("El espejo solo se reinicia en el servidor de la nube")
    conn = db.connection()
    vaciadas = _vaciar_datos_de_negocio(conn)
    # Espejo nuevo: otro identificador (la caja reenviará todo) y sin caja vinculada
    conn.execute(text("DELETE FROM configuracion WHERE clave IN ('sync_espejo_id', 'sync_instalacion_vinculada')"))
    nuevo = espejo_id(conn)
    db.commit()
    return {"tablas_vaciadas": vaciadas, "espejo_id": nuevo}


# ------------------------------------------------------------------ estado
def obtener_estado_sync(db: Session, modo: str = "LOCAL") -> SyncEstadoOut:
    """Métricas del motor de sincronización.

    `pendientes` cuenta lo que este servidor todavía tiene por entregar al otro lado:
    en la caja, lo que falta subir; en la nube, lo que la caja aún no ha descargado.
    """
    from app.services.sync_worker import get_worker_status

    propio = replicacion.origen_propio()
    base = db.query(func.count(RegistroSync.id))
    total = base.scalar() or 0
    pendientes = base.filter(RegistroSync.estado == "PENDIENTE", RegistroSync.origen == propio).scalar() or 0
    aplicadas = base.filter(RegistroSync.estado == "APLICADO").scalar() or 0
    conflictos = (
        base.filter(RegistroSync.estado.in_(("CONFLICTO", "ERROR", "ERROR_SERVIDOR"))).scalar() or 0
    )
    ultima = db.query(func.max(RegistroSync.sincronizado_en)).scalar()

    worker_st = get_worker_status()
    return SyncEstadoOut(
        cerebro_modo=modo,
        total_operaciones=int(total),
        pendientes=int(pendientes),
        aplicadas=int(aplicadas),
        conflictos=int(conflictos),
        ultima_sincronizacion=ultima,
        online=worker_st.get("online", True),
        sincronizando=worker_st.get("sincronizando", False),
        ultimo_error=worker_st.get("ultimo_error"),
        sucursal_id=getattr(settings, "SUCURSAL_ID", "SUC-01"),
    )

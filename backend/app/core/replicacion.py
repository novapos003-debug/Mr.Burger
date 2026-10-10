"""Réplica por filas entre el cerebro LOCAL (caja del restaurante) y el espejo en la NUBE.

Principio: en vez de mensajes escritos a mano por cada tipo de operación (que perdían campos
y olvidaban casos), cada cambio confirmado en la base de datos genera una operación con la
FILA COMPLETA tal como quedó. El otro lado la aplica con un "insertar o actualizar" por clave
primaria. Así todo lo que se guarda se replica, con sus horas y valores exactos.

- Captura: ganchos de SQLAlchemy registran qué filas tocó cada transacción y, justo antes de
  confirmar, guardan su estado final en `registro_sync` dentro de la MISMA transacción (patrón
  Outbox: si la venta se guardó, su réplica también; si se deshizo, no queda nada).
- Aplicación: SQL directo por conexión. No pasa por los ganchos, así que aplicar una operación
  recibida nunca genera una operación de vuelta (no hay bucles).
- Identificadores: la nube numera desde ID_BASE_NUBE, así lo creado en el panel web nunca
  choca con lo creado en la caja.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import event, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base

logger = logging.getLogger("replicacion")

TIPO_FILA = "FILA"
TIPO_BORRAR = "BORRAR"
TIPOS_REPLICA = (TIPO_FILA, TIPO_BORRAR)

# La cola de sincronización no se replica a sí misma
TABLAS_EXCLUIDAS = {"registro_sync"}

# Claves de `configuracion` que son internas de cada instalación (banderas de migración y
# cursores de sincronización). Si se replicaran, un lado creería haber hecho lo del otro.
PREFIJOS_CONFIG_INTERNOS = ("sync_", "migracion_")

# Los identificadores creados en la nube empiezan aquí; los de la caja van por debajo.
ID_BASE_NUBE = 1_000_000

_CLAVE_INFO = "_replicacion_pendiente"


# ------------------------------------------------------------------ utilidades
def origen_propio() -> str:
    return "NUBE" if settings.MODO_CEREBRO == "NUBE" else "LOCAL"


def captura_activa() -> bool:
    """La nube siempre registra sus cambios (para que bajen a la caja). La caja solo registra
    si tiene un espejo configurado; sin él las operaciones se acumularían para siempre."""
    if settings.MODO_CEREBRO == "NUBE":
        return True
    return bool(settings.CLOUD_SYNC_ENABLED and settings.CLOUD_SYNC_URL)


def tabla_replicable(nombre: str) -> bool:
    return nombre in Base.metadata.tables and nombre not in TABLAS_EXCLUIDAS


def _fila_interna(tabla: str, pk: dict) -> bool:
    if tabla != "configuracion":
        return False
    return str(pk.get("clave", "")).startswith(PREFIJOS_CONFIG_INTERNOS)


def _orden_tablas() -> dict[str, int]:
    """Orden que respeta las llaves foráneas: los padres antes que los hijos."""
    return {t.name: i for i, t in enumerate(Base.metadata.sorted_tables)}


def pk_texto(pk: dict) -> str:
    return "|".join(str(pk[k]) for k in sorted(pk))[:64]


def _columnas_pk(tabla: str) -> list[str]:
    return [c.name for c in Base.metadata.tables[tabla].primary_key.columns]


def _where_pk(tabla: str) -> str:
    return " AND ".join(f'"{c}" = :pk_{c}' for c in _columnas_pk(tabla))


def _params_pk(pk: dict) -> dict:
    return {f"pk_{k}": v for k, v in pk.items()}


# ------------------------------------------------------------------ captura
def _marcar(session: Session, tabla: str, pk: dict, accion: str) -> None:
    if session.info.get("_replicacion_omitir"):
        return  # la sesión está aplicando operaciones recibidas del otro lado
    if not tabla_replicable(tabla) or _fila_interna(tabla, pk):
        return
    if any(v is None for v in pk.values()):
        return
    pendiente = session.info.setdefault(_CLAVE_INFO, {})
    pendiente[(tabla, tuple(sorted(pk.items())))] = accion


def _pk_de_objeto(obj) -> dict:
    tabla = obj.__table__
    return {c.name: getattr(obj, c.key, None) for c in tabla.primary_key.columns}


@event.listens_for(Session, "before_flush")
def _antes_de_flush(session: Session, _ctx, _instancias) -> None:
    """Las filas MODIFICADAS se anotan antes del flush: después, los campos asignados con una
    expresión SQL (p. ej. `cancelado_en = func.now()`) quedan expirados y el cambio no se ve."""
    if not captura_activa():
        return
    for obj in session.dirty:
        if hasattr(obj, "__table__") and session.is_modified(obj, include_collections=False):
            _marcar(session, obj.__table__.name, _pk_de_objeto(obj), TIPO_FILA)


@event.listens_for(Session, "after_flush")
def _tras_flush(session: Session, _ctx) -> None:
    """Las filas NUEVAS se anotan después del flush, cuando ya tienen su id."""
    if not captura_activa():
        return
    for obj in session.new:
        if hasattr(obj, "__table__"):
            _marcar(session, obj.__table__.name, _pk_de_objeto(obj), TIPO_FILA)
    for obj in session.deleted:
        if hasattr(obj, "__table__"):
            _marcar(session, obj.__table__.name, _pk_de_objeto(obj), TIPO_BORRAR)


@event.listens_for(Session, "do_orm_execute")
def _operacion_masiva(estado) -> None:
    """UPDATE/DELETE masivos (`query.update()`, `query.delete()`) no pasan por el flush.
    Antes de ejecutarlos se anotan las claves de las filas que van a tocar."""
    if not (estado.is_update or estado.is_delete) or not captura_activa():
        return
    try:
        tabla = estado.statement.table
        if not tabla_replicable(tabla.name):
            return
        columnas = list(tabla.primary_key.columns)
        consulta = select(*columnas)
        if estado.statement.whereclause is not None:
            consulta = consulta.where(estado.statement.whereclause)
        conn = estado.session.connection()
        try:
            filas = conn.execute(consulta).all()
        except Exception:
            filas = conn.execute(consulta, estado.parameters or {}).all()
        accion = TIPO_BORRAR if estado.is_delete else TIPO_FILA
        for fila in filas:
            _marcar(estado.session, tabla.name, {c.name: v for c, v in zip(columnas, fila)}, accion)
    except Exception as exc:  # nunca bloquear la operación de negocio por la réplica
        logger.warning("No se pudieron anotar filas de una operación masiva: %s", exc)


@event.listens_for(Session, "before_commit")
def _antes_de_confirmar(session: Session) -> None:
    if not captura_activa():
        return
    session.flush()  # asegura ids y que el after_flush haya anotado todo
    pendiente: dict = session.info.pop(_CLAVE_INFO, None) or {}
    if not pendiente:
        return

    orden = _orden_tablas()
    borrados = sorted(
        (k for k, a in pendiente.items() if a == TIPO_BORRAR), key=lambda k: -orden.get(k[0], 0)
    )
    filas = sorted((k for k, a in pendiente.items() if a == TIPO_FILA), key=lambda k: (orden.get(k[0], 0), str(k[1])))

    conn = session.connection()
    escritas = 0
    # Primero los borrados (hijos antes que padres) y luego las filas (padres antes que hijos)
    for tabla, pk_items in borrados:
        escritas += encolar_borrado(conn, tabla, dict(pk_items))
    for tabla, pk_items in filas:
        escritas += encolar_fila(conn, tabla, dict(pk_items))
    if escritas:
        session.info["_replicacion_despertar"] = True


@event.listens_for(Session, "after_commit")
def _tras_confirmar(session: Session) -> None:
    if session.info.pop("_replicacion_despertar", False):
        from app.services.sync_worker import despertar_worker

        despertar_worker()


@event.listens_for(Session, "after_rollback")
def _tras_deshacer(session: Session) -> None:
    session.info.pop(_CLAVE_INFO, None)
    session.info.pop("_replicacion_despertar", None)


# ------------------------------------------------------------------ cola de salida
_SQL_INSERTAR_OP = text(
    "INSERT INTO registro_sync (op_id, sucursal_id, dispositivo_id, tipo, entidad, entidad_id, "
    "entidad_uuid, payload, origen, estado, reintentos) VALUES (:op_id, :suc, :disp, :tipo, :ent, "
    ":ent_id, :ent_uuid, CAST(:payload AS jsonb), :origen, 'PENDIENTE', 0)"
)


def _insertar_op(conn, tipo: str, tabla: str, pk: dict, payload: dict) -> None:
    ent_id = pk.get("id") if isinstance(pk.get("id"), int) else None
    conn.execute(
        _SQL_INSERTAR_OP,
        {
            "op_id": str(uuid.uuid4()),
            "suc": settings.SUCURSAL_ID or "SUC-01",
            "disp": origen_propio(),
            "tipo": tipo,
            "ent": tabla,
            "ent_id": ent_id,
            "ent_uuid": pk_texto(pk),
            "payload": json.dumps(payload, default=str),
            "origen": origen_propio(),
        },
    )


def encolar_fila(conn, tabla: str, pk: dict) -> int:
    """Guarda en la cola el estado actual de una fila. Devuelve 1 si la encoló."""
    if not tabla_replicable(tabla) or _fila_interna(tabla, pk):
        return 0
    fila = conn.execute(
        text(f'SELECT row_to_json(t) FROM "{tabla}" t WHERE {_where_pk(tabla)}'), _params_pk(pk)
    ).scalar()
    if fila is None:  # se creó y se borró en la misma transacción
        return 0
    _insertar_op(conn, TIPO_FILA, tabla, pk, {"pk": pk, "fila": fila})
    return 1


def encolar_borrado(conn, tabla: str, pk: dict) -> int:
    if not tabla_replicable(tabla) or _fila_interna(tabla, pk):
        return 0
    _insertar_op(conn, TIPO_BORRAR, tabla, pk, {"pk": pk})
    return 1


def encolar_snapshot_completo(conn) -> int:
    """Encola TODAS las filas de todas las tablas (padres primero) para reconstruir el espejo."""
    total = 0
    for tabla in Base.metadata.sorted_tables:
        if not tabla_replicable(tabla.name):
            continue
        pks = _columnas_pk(tabla.name)
        pk_json = ", ".join(f"'{c}', t.\"{c}\"" for c in pks)
        ent_id = 't."id"' if pks == ["id"] else "NULL"
        ent_uuid = " || '|' || ".join(f't."{c}"::text' for c in sorted(pks))
        filtro = ""
        if tabla.name == "configuracion":
            filtro = "WHERE " + " AND ".join(f"t.clave NOT LIKE '{p}%'" for p in PREFIJOS_CONFIG_INTERNOS)
        orden = ", ".join(f't."{c}"' for c in pks)
        res = conn.execute(
            text(
                f"""
                INSERT INTO registro_sync (op_id, sucursal_id, dispositivo_id, tipo, entidad, entidad_id,
                                           entidad_uuid, payload, origen, estado, reintentos)
                SELECT gen_random_uuid()::text, :suc, :disp, '{TIPO_FILA}', '{tabla.name}', {ent_id},
                       left({ent_uuid}, 64),
                       jsonb_build_object('pk', jsonb_build_object({pk_json}), 'fila', to_jsonb(t)),
                       :origen, 'PENDIENTE', 0
                FROM (SELECT * FROM "{tabla.name}" t {filtro} ORDER BY {orden}) t
                """
            ),
            {"suc": settings.SUCURSAL_ID or "SUC-01", "disp": origen_propio(), "origen": origen_propio()},
        )
        total += res.rowcount or 0
    return total


# ------------------------------------------------------------------ aplicación
_cache_columnas: dict[str, list[str]] = {}


def _columnas_reales(conn, tabla: str) -> list[str]:
    """Columnas que la tabla tiene de verdad en esta base. Se consultan una vez por tabla: las
    columnas solo cambian al arrancar (migraciones), antes de que empiece la sincronización."""
    if tabla in _cache_columnas:
        return _cache_columnas[tabla]
    filas = conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = :t ORDER BY ordinal_position"
        ),
        {"t": tabla},
    ).all()
    columnas = [f[0] for f in filas]
    if columnas:
        _cache_columnas[tabla] = columnas
    return columnas


def _existe(conn, tabla: str, pk: dict) -> bool:
    return (
        conn.execute(text(f'SELECT 1 FROM "{tabla}" WHERE {_where_pk(tabla)}'), _params_pk(pk)).first()
        is not None
    )


def _upsert(conn, tabla: str, fila: dict, excluir_en_update: set[str] | None = None) -> None:
    pks = _columnas_pk(tabla)
    columnas = [c for c in _columnas_reales(conn, tabla) if c in fila]
    if not columnas or any(p not in columnas for p in pks):
        raise ValueError(f"Fila de '{tabla}' sin clave primaria o sin columnas reconocibles")
    excluir = set(pks) | (excluir_en_update or set())
    lista = ", ".join(f'"{c}"' for c in columnas)
    actualizables = [c for c in columnas if c not in excluir]
    accion = (
        "DO UPDATE SET " + ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in actualizables)
        if actualizables
        else "DO NOTHING"
    )
    conn.execute(
        text(
            f'INSERT INTO "{tabla}" ({lista}) '
            f'SELECT {lista} FROM json_populate_record(NULL::"{tabla}", CAST(:fila AS json)) '
            f'ON CONFLICT ({", ".join(chr(34) + p + chr(34) for p in pks)}) {accion}'
        ),
        {"fila": json.dumps(fila, default=str)},
    )


def aplicar_operacion(conn, tipo: str, tabla: str, payload: dict, *, origen_op: str) -> list[tuple[str, dict]]:
    """Aplica una operación de réplica recibida del otro lado.

    Devuelve las filas (tabla, pk) cuyo estado local resultante debe subirse de vuelta para
    que ambos lados terminen idénticos. Solo ocurre en la caja al aplicar cambios de la nube.
    """
    if not tabla_replicable(tabla):
        raise ValueError(f"Tabla no replicable: {tabla}")
    pk = payload.get("pk") or {}
    if not pk or set(pk) != set(_columnas_pk(tabla)):
        raise ValueError(f"Clave primaria inválida para '{tabla}'")
    if _fila_interna(tabla, pk):
        return []

    en_caja_desde_nube = origen_propio() == "LOCAL" and origen_op == "NUBE"

    if tipo == TIPO_BORRAR:
        conn.execute(text(f'DELETE FROM "{tabla}" WHERE {_where_pk(tabla)}'), _params_pk(pk))
        return []

    if tipo != TIPO_FILA:
        raise ValueError(f"Tipo de operación desconocido: {tipo}")

    fila = payload.get("fila")
    if not isinstance(fila, dict):
        raise ValueError("Operación FILA sin contenido")

    if not en_caja_desde_nube:
        _upsert(conn, tabla, fila)
        return []

    # ---- La caja aplica un cambio hecho en el panel web ----
    # El STOCK lo manda la caja: es donde se cocina y se vende. De la nube solo se aceptan
    # los MOVIMIENTOS (compra, ajuste, merma hechos desde la web), que se suman como diferencia.
    if tabla == "ingrediente":
        if _existe(conn, tabla, pk):
            _upsert(conn, tabla, fila, excluir_en_update={"stock_actual"})
        else:
            _upsert(conn, tabla, {**fila, "stock_actual": 0})
        return [(tabla, pk)]

    if tabla == "movimiento_inventario":
        nuevo = not _existe(conn, tabla, pk)
        _upsert(conn, tabla, fila)
        devolver = [(tabla, pk)]
        if nuevo and fila.get("ingrediente_id") is not None and fila.get("cantidad") is not None:
            saldos = conn.execute(
                text(
                    "UPDATE ingrediente SET stock_actual = COALESCE(stock_actual, 0) + CAST(:c AS numeric) "
                    "WHERE id = :i RETURNING stock_actual - CAST(:c AS numeric), stock_actual"
                ),
                {"c": str(fila["cantidad"]), "i": fila["ingrediente_id"]},
            ).first()
            if saldos:
                conn.execute(
                    text(
                        f'UPDATE "{tabla}" SET saldo_anterior = :a, saldo_nuevo = :n WHERE {_where_pk(tabla)}'
                    ),
                    {"a": saldos[0], "n": saldos[1], **_params_pk(pk)},
                )
                devolver.insert(0, ("ingrediente", {"id": fila["ingrediente_id"]}))
        return devolver

    _upsert(conn, tabla, fila)
    return [(tabla, pk)]


# ------------------------------------------------------------------ secuencias
def reservar_rango_nube(conn) -> None:
    """En la nube, todas las secuencias arrancan en ID_BASE_NUBE (idempotente)."""
    for tabla in Base.metadata.sorted_tables:
        if _columnas_pk(tabla.name) != ["id"]:
            continue
        seq = conn.execute(text("SELECT pg_get_serial_sequence(:t, 'id')"), {"t": tabla.name}).scalar()
        if not seq:
            continue
        actual = conn.execute(text(f"SELECT last_value FROM {seq}")).scalar() or 0
        if actual < ID_BASE_NUBE:
            conn.execute(text("SELECT setval(CAST(:s AS regclass), :v, true)"), {"s": seq, "v": ID_BASE_NUBE})


def ajustar_secuencias_locales(conn) -> None:
    """En la caja, cada secuencia continúa después del mayor id PROPIO (por debajo del rango de
    la nube). Evita 'llave duplicada' tras restaurar un respaldo o cargar datos con id fijo."""
    for tabla in Base.metadata.sorted_tables:
        if _columnas_pk(tabla.name) != ["id"]:
            continue
        seq = conn.execute(text("SELECT pg_get_serial_sequence(:t, 'id')"), {"t": tabla.name}).scalar()
        if not seq:
            continue
        maximo = conn.execute(
            text(f'SELECT COALESCE(MAX(id), 0) FROM "{tabla.name}" WHERE id < :base'), {"base": ID_BASE_NUBE}
        ).scalar()
        actual, usada = conn.execute(text(f"SELECT last_value, is_called FROM {seq}")).first()
        siguiente_actual = actual + 1 if usada else actual
        if siguiente_actual <= maximo or siguiente_actual > ID_BASE_NUBE:
            conn.execute(
                text("SELECT setval(CAST(:s AS regclass), :v, :c)"),
                {"s": seq, "v": max(maximo, 1), "c": maximo > 0},
            )

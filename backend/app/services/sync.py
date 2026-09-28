from app.database import safe_commit
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import RegistroSync, Usuario
from app.schemas.sync import (
    SyncEstadoOut,
    SyncOpIn,
    SyncOpOut,
    SyncPushIn,
    SyncPushOut,
)
from app.services.historial import registrar


def procesar_push(db: Session, data: SyncPushIn, usuario: Usuario) -> SyncPushOut:
    """Procesa un lote de operaciones offline enviadas con UUID único.
    
    Reglas del Documento Maestro (Sección 3):
    1. Idempotencia absoluta: si op_id ya existe, se ignora como duplicado.
    2. Autoridad:
       - Lo que vende (pedidos, rondas, pagos) manda el LOCAL.
       - Lo que configura (precios, productos, recetas) manda la NUBE.
    """
    procesadas = 0
    duplicadas = 0
    conflictos = 0
    resultado_ops: list[RegistroSync] = []

    for op in data.operaciones:
        # Chequeo de idempotencia por UUID
        existente = db.query(RegistroSync).filter(RegistroSync.op_id == op.op_id).first()
        if existente:
            duplicadas += 1
            resultado_ops.append(existente)
            continue

        estado = "APLICADO"
        nota_resolucion = None

        # Evaluación de regla de autoridad
        if op.origen == "NUBE" and op.entidad in ("pedido", "pago", "detalle_pedido"):
            # Conflicto: la nube intentó sobreescribir ventas locales
            estado = "CONFLICTO"
            nota_resolucion = "Rechazado: Las transacciones locales de venta tienen autoridad absoluta"
            conflictos += 1
        else:
            procesadas += 1

        registro = RegistroSync(
            op_id=op.op_id,
            sucursal_id=getattr(op, "sucursal_id", "SUC-01"),
            dispositivo_id=op.dispositivo_id,
            tipo=op.tipo,
            entidad=op.entidad,
            entidad_id=op.entidad_id,
            entidad_uuid=getattr(op, "entidad_uuid", None),
            payload=op.payload,
            origen=op.origen,
            estado=estado,
            resolucion_nota=nota_resolucion,
            sincronizado_en=func.now() if estado == "APLICADO" else None,
        )
        db.add(registro)
        db.flush()
        resultado_ops.append(registro)

        registrar(
            db,
            usuario,
            "SYNC_PUSH",
            "registro_sync",
            registro.id,
            f"op_id={op.op_id} tipo={op.tipo} estado={estado} disp={op.dispositivo_id}",
        )

    safe_commit(db)
    for r in resultado_ops:
        db.refresh(r)

    return SyncPushOut(
        procesadas=procesadas,
        duplicadas=duplicadas,
        conflictos=conflictos,
        operaciones=[SyncOpOut.model_validate(r) for r in resultado_ops],
    )


def encolar_sync(
    db: Session,
    tipo: str,
    entidad: str,
    payload: dict,
    entidad_id: int | None = None,
    entidad_uuid: str | None = None,
    dispositivo_id: str = "CAJA-LOCAL",
    sucursal_id: str = "SUC-01",
) -> RegistroSync:
    """Encola una operación en registro_sync (Patrón Outbox) para sincronización automática con la nube."""
    import uuid
    from app.config import settings

    op_id = str(uuid.uuid4())
    registro = RegistroSync(
        op_id=op_id,
        sucursal_id=sucursal_id or getattr(settings, "SUCURSAL_ID", "SUC-01"),
        dispositivo_id=dispositivo_id,
        tipo=tipo,
        entidad=entidad,
        entidad_id=entidad_id,
        entidad_uuid=entidad_uuid or str(uuid.uuid4()),
        payload=payload,
        origen="LOCAL",
        estado="PENDIENTE",
    )
    db.add(registro)
    return registro


def obtener_pull(
    db: Session,
    since: datetime | None = None,
    origen_filtro: str | None = None,
    limit: int = 100,
) -> list[SyncOpOut]:
    """Obtiene operaciones registradas desde una fecha/hora para sincronizar terminales."""
    q = db.query(RegistroSync).order_by(RegistroSync.creado_en.asc())
    if since:
        q = q.filter(RegistroSync.creado_en > since)
    if origen_filtro:
        q = q.filter(RegistroSync.origen == origen_filtro)

    ops = q.limit(limit).all()
    return [SyncOpOut.model_validate(o) for o in ops]


def obtener_estado_sync(db: Session, modo: str = "LOCAL") -> SyncEstadoOut:
    """Métricas del motor de sincronización."""
    from app.config import settings
    from app.services.sync_worker import get_worker_status

    total = db.query(func.count(RegistroSync.id)).scalar() or 0
    pendientes = db.query(func.count(RegistroSync.id)).filter(RegistroSync.estado == "PENDIENTE").scalar() or 0
    aplicadas = db.query(func.count(RegistroSync.id)).filter(RegistroSync.estado == "APLICADO").scalar() or 0
    conflictos = db.query(func.count(RegistroSync.id)).filter(RegistroSync.estado == "CONFLICTO").scalar() or 0
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

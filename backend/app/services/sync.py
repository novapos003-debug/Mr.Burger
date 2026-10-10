import logging
import re
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.tiempo import fecha_local
from app.database import safe_commit
from app.models import (
    Cierre,
    DetallePedido,
    DetalleReceta,
    Ingrediente,
    Mesa,
    MovimientoCaja,
    MovimientoInventario,
    Pago,
    Pedido,
    RegistroSync,
    Usuario,
    Vale,
)
from app.schemas.sync import (
    SyncEstadoOut,
    SyncOpIn,
    SyncOpOut,
    SyncOpResultado,
    SyncPushIn,
    SyncPushOut,
)
from app.services.historial import registrar

logger = logging.getLogger("sync")


def _resolver_usuario_id(db: Session, op, payload: dict) -> int:
    """Pedido.usuario_id es obligatorio en la nube.

    Las operaciones encoladas antes de este arreglo no lo traen en el payload, pero sí
    viajan con dispositivo_id = 'USER_<id>' / 'CAJA_<id>'. Orden de búsqueda:
    payload -> sufijo numérico del dispositivo -> usuario 'admin' -> primer usuario.
    """
    candidatos = [payload.get("usuario_id")]
    m = re.search(r"(\d+)$", getattr(op, "dispositivo_id", "") or "")
    if m:
        candidatos.append(m.group(1))
    for c in candidatos:
        try:
            uid = int(c)
        except (TypeError, ValueError):
            continue
        if db.get(Usuario, uid):
            return uid
    fallback = (
        db.query(Usuario).filter(Usuario.usuario == "admin").first()
        or db.query(Usuario).order_by(Usuario.id.asc()).first()
    )
    if not fallback:
        raise ValueError("No hay usuarios en la nube a quienes asignar el pedido")
    return fallback.id


def _fecha(valor) -> date:
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and valor[:10]:
        return date.fromisoformat(valor[:10])
    return fecha_local()


def asimilar_operacion(db: Session, op) -> None:
    """Asimila materialmente una operación en las tablas de negocio de la Nube (Render).

    Si la operación no se puede aplicar lanza una excepción: `procesar_push` la ejecuta dentro
    de un SAVEPOINT, así un fallo solo descarta esa operación y no el lote completo.
    """
    tipo = op.tipo
    payload = op.payload
    if not payload or not isinstance(payload, dict):
        return

    try:
        if tipo in ("CREAR_PEDIDO", "AGREGAR_RONDA"):
            # AGREGAR_RONDA identifica el pedido con 'pedido_id' (no con 'id')
            pid = payload.get("id") or payload.get("pedido_id")
            pedido = db.get(Pedido, pid) if pid else None
            if not pedido:
                if tipo == "AGREGAR_RONDA":
                    raise ValueError(f"AGREGAR_RONDA: el pedido {pid} todavía no existe en la nube")
                mesa_id = payload.get("mesa_id")
                if mesa_id and not db.get(Mesa, mesa_id):
                    mesa_id = None
                pedido = Pedido(
                    id=pid,
                    consecutivo=payload.get("consecutivo", 1),
                    fecha_dia=_fecha(payload.get("fecha_dia")),
                    canal=payload.get("canal") or "MOSTRADOR",
                    tipo_consumo=payload.get("tipo_consumo") or "LOCAL",
                    mesa_id=mesa_id,
                    usuario_id=_resolver_usuario_id(db, op, payload),
                    cliente=payload.get("cliente"),
                    subtotal=Decimal(str(payload.get("subtotal") or 0)),
                    iva=Decimal(str(payload.get("iva") or 0)),
                    total=Decimal(str(payload.get("total") or 0)),
                    estado=payload.get("estado") or "ENVIADO_A_COCINA",
                )
                db.add(pedido)
                db.flush()
            else:
                pedido.estado = payload.get("estado") or pedido.estado
                total = payload.get("total", payload.get("nuevo_total"))
                if total is not None:
                    pedido.total = Decimal(str(total))

            for d in payload.get("detalles", []):
                prod_id = d.get("producto_id")
                det_existente = (
                    db.query(DetallePedido)
                    .filter(
                        DetallePedido.pedido_id == pedido.id,
                        DetallePedido.producto_id == prod_id,
                        DetallePedido.ronda == d.get("ronda", 1),
                    )
                    .first()
                )
                if not det_existente:
                    nuevo_d = DetallePedido(
                        pedido_id=pedido.id,
                        producto_id=prod_id,
                        cantidad=Decimal(str(d.get("cantidad", 1))),
                        precio_unitario=Decimal(str(d.get("precio_unitario", 0))),
                        ronda=d.get("ronda", 1),
                        # el payload local manda "estado": null -> columna NOT NULL
                        estado=d.get("estado") or "ENVIADO",
                    )
                    db.add(nuevo_d)

        elif tipo == "COBRO_PEDIDO":
            pago_id = payload.get("id")
            pago = db.get(Pago, pago_id) if pago_id else None
            if not pago:
                pago = Pago(
                    id=pago_id,
                    pedido_id=payload.get("pedido_id"),
                    metodo=payload.get("metodo", "EFECTIVO"),
                    monto=Decimal(str(payload.get("monto", 0))),
                    recibido=Decimal(str(payload.get("recibido", 0))) if payload.get("recibido") is not None else None,
                    cambio=Decimal(str(payload.get("cambio", 0))) if payload.get("cambio") is not None else None,
                    didi_orden_id=payload.get("didi_orden_id"),
                    estado="VALIDO",
                )
                db.add(pago)
            ped = db.get(Pedido, payload.get("pedido_id"))
            if ped:
                ped.estado = "PAGADO"
                ped.pagado_en = ped.pagado_en or func.now()

        elif tipo == "MOVIMIENTO_CAJA":
            m_id = payload.get("id")
            mov = db.get(MovimientoCaja, m_id) if m_id else None
            if not mov:
                mov = MovimientoCaja(
                    id=m_id,
                    usuario_id=payload.get("usuario_id", 1),
                    tipo=payload.get("tipo", "SALIDA"),
                    categoria=payload.get("categoria", "OTRO"),
                    concepto=payload.get("concepto", "Movimiento sincronizado"),
                    descripcion=payload.get("descripcion", ""),
                    valor=Decimal(str(payload.get("valor", 0))),
                    cierre_id=payload.get("cierre_id"),
                )
                db.add(mov)

        elif tipo in ("ABRIR_TURNO", "CIERRE_TURNO"):
            c_id = payload.get("id")
            cierre = db.get(Cierre, c_id) if c_id else None
            abierto_en_val = payload.get("abierto_en") or func.now()
            cerrado_en_val = func.now() if payload.get("cerrado_en") == "now()" else payload.get("cerrado_en")
            if not cierre:
                cierre = Cierre(
                    id=c_id,
                    usuario_id=payload.get("usuario_id", 1),
                    abierto_en=abierto_en_val,
                    cerrado_en=cerrado_en_val,
                    total_ventas=Decimal(str(payload.get("total_ventas", 0))),
                    total_efectivo=Decimal(str(payload.get("total_efectivo", 0))),
                    total_tarjeta=Decimal(str(payload.get("total_tarjeta", 0))),
                    total_transferencia=Decimal(str(payload.get("total_transferencia", 0))),
                    total_didi_efectivo=Decimal(str(payload.get("total_didi_efectivo", 0))),
                    total_didi_tarjeta=Decimal(str(payload.get("total_didi_tarjeta", 0))),
                    total_entradas_caja=Decimal(str(payload.get("total_entradas_caja", 0))),
                    total_salidas_caja=Decimal(str(payload.get("total_salidas_caja", 0))),
                    total_efectivo_final=Decimal(str(payload.get("total_efectivo_final", 0))),
                    notas=payload.get("notas"),
                )
                db.add(cierre)
            else:
                if payload.get("cerrado_en"):
                    cierre.cerrado_en = cerrado_en_val
                for k, v in payload.items():
                    if hasattr(cierre, k) and v is not None and k not in ("id", "abierto_en", "cerrado_en"):
                        try:
                            setattr(cierre, k, Decimal(str(v)) if isinstance(v, (int, float)) else v)
                        except Exception:
                            pass

        elif tipo == "DESCUENTO_STOCK":
            ing_id = payload.get("ingrediente_id")
            ing = db.get(Ingrediente, ing_id) if ing_id else None
            if ing and payload.get("stock_actual_checkpoint") is not None:
                ing.stock_actual = Decimal(str(payload["stock_actual_checkpoint"]))

        elif tipo in ("CREAR_USUARIO", "USUARIO_CREADO"):
            u_id = payload.get("id")
            u = db.get(Usuario, u_id) if u_id else None
            if not u:
                u = Usuario(
                    id=u_id,
                    nombre=payload.get("nombre", ""),
                    usuario=payload.get("usuario", ""),
                    rol_id=payload.get("rol_id", 2),
                    password_hash=payload.get("password_hash", ""),
                    activo=payload.get("activo", True),
                    fijado=payload.get("fijado", False),
                    es_demo=payload.get("es_demo", False),
                )
                db.add(u)

        elif tipo == "MODIFICAR_PASSWORD":
            u_id = payload.get("usuario_id")
            u = db.get(Usuario, u_id) if u_id else None
            if u and payload.get("nueva_password_hash"):
                u.password_hash = payload["nueva_password_hash"]

        elif tipo == "MODIFICAR_RECETA":
            p_id = payload.get("producto_id")
            lineas = payload.get("lineas", [])
            if p_id and isinstance(lineas, list):
                db.query(DetalleReceta).filter(DetalleReceta.product_id == p_id).delete()
                for l in lineas:
                    db.add(
                        DetalleReceta(
                            product_id=p_id,
                            ingrediente_id=l.get("ingrediente_id"),
                            cantidad=Decimal(str(l.get("cantidad", 1))),
                            unidad=l.get("unidad", "UNIDAD"),
                            solo_llevar=l.get("solo_llevar", False),
                        )
                    )
    except Exception as e:
        # Antes se tragaba el error y dejaba la sesión inutilizable (-> HTTP 500 para TODO el lote).
        logger.warning("No se pudo asimilar la operación sync %s: %s", tipo, str(e).splitlines()[0][:300])
        raise


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
    errores = 0
    resultado_ops: list[RegistroSync] = []
    resultados: list[SyncOpResultado] = []

    for op in data.operaciones:
        # Chequeo de idempotencia por UUID
        existente = db.query(RegistroSync).filter(RegistroSync.op_id == op.op_id).first()
        if existente:
            duplicadas += 1
            resultado_ops.append(existente)
            resultados.append(SyncOpResultado(op_id=op.op_id, estado="DUPLICADO"))
            continue

        estado = "APLICADO"
        nota_resolucion = None

        # Evaluación de regla de autoridad
        if op.origen == "NUBE" and op.entidad in ("pedido", "pago", "detalle_pedido"):
            # Conflicto: la nube intentó sobreescribir ventas locales
            estado = "CONFLICTO"
            nota_resolucion = "Rechazado: Las transacciones locales de venta tienen autoridad absoluta"

        try:
            # SAVEPOINT por operación: si una venta falla, solo se descarta ESA operación.
            # Antes un solo fallo dejaba la sesión inutilizable y tumbaba el lote completo
            # (HTTP 500/409), con lo cual la cola local quedaba atascada para siempre.
            with db.begin_nested():
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

                # Asimilar materialmente en tablas de dominio en la nube
                if estado == "APLICADO":
                    asimilar_operacion(db, op)

                registrar(
                    db,
                    usuario,
                    "SYNC_PUSH",
                    "registro_sync",
                    registro.id,
                    f"op_id={op.op_id} tipo={op.tipo} estado={estado} disp={op.dispositivo_id}",
                )
        except Exception as e:
            errores += 1
            detalle = (str(e).splitlines() or [""])[0][:300] or type(e).__name__
            resultados.append(SyncOpResultado(op_id=op.op_id, estado="ERROR", error=detalle))
            continue

        if estado == "CONFLICTO":
            conflictos += 1
        else:
            procesadas += 1
        resultado_ops.append(registro)
        resultados.append(SyncOpResultado(op_id=op.op_id, estado=estado))

    safe_commit(db)
    for r in resultado_ops:
        db.refresh(r)

    return SyncPushOut(
        procesadas=procesadas,
        duplicadas=duplicadas,
        conflictos=conflictos,
        errores=errores,
        operaciones=[SyncOpOut.model_validate(r) for r in resultado_ops],
        resultados=resultados,
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


def reconciliar_usuarios_locales(db: Session) -> int:
    """Inspecciona y encola automáticamente usuarios locales creados previamente que no estén en la nube."""
    from app.models.usuario import Usuario

    SEEDS_SISTEMA = {"admin", "caja", "mesero", "cocina"}
    usuarios_activos = db.query(Usuario).filter(Usuario.activo == True).all()
    encolados = 0

    for u in usuarios_activos:
        if u.usuario in SEEDS_SISTEMA:
            continue

        ya_en_sync = (
            db.query(RegistroSync)
            .filter(
                RegistroSync.tipo == "CREAR_USUARIO",
                RegistroSync.entidad_id == u.id,
            )
            .first()
        )
        if not ya_en_sync:
            encolar_sync(
                db,
                tipo="CREAR_USUARIO",
                entidad="usuario",
                payload={
                    "id": u.id,
                    "nombre": u.nombre,
                    "usuario": u.usuario,
                    "rol_id": u.rol_id,
                    "password_hash": u.password_hash,
                    "activo": u.activo,
                    "fijado": u.fijado,
                    "es_demo": u.es_demo,
                },
                entidad_id=u.id,
                dispositivo_id="SISTEMA_RECONCILIACION",
            )
            encolados += 1

    if encolados > 0:
        safe_commit(db)
        import logging
        logging.info("Reconciliación: %d usuario(s) local(es) encolados para sincronización en la nube", encolados)

    return encolados


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

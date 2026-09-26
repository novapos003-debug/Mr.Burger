from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func

from app.models import DetallePedido, MovimientoCaja, Pago, Pedido, Preparado, Producto, Usuario
from app.schemas.preparados import PreparadoOut
from app.services.caja import _monto, turno_abierto
from app.services.historial import registrar
from app.services.pedidos import calcular_totales


def minutos_espera(creado_en: datetime | None) -> int:
    """Calcula los minutos transcurridos desde que el preparado entró en espera."""
    if not creado_en:
        return 0
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)
    ahora = datetime.now(timezone.utc)
    return max(0, int((ahora - creado_en).total_seconds() / 60))


def preparado_a_out(p: Preparado) -> PreparadoOut:
    """Convierte un modelo Preparado en su schema de salida con datos enriquecidos."""
    return PreparadoOut(
        id=p.id,
        producto_id=p.producto_id,
        producto_nombre=p.producto.nombre if p.producto else None,
        pedido_origen_id=p.pedido_origen_id,
        pedido_origen_consecutivo=p.pedido_origen.consecutivo if p.pedido_origen else None,
        detalle_origen_id=p.detalle_origen_id,
        variacion_snapshot=p.variacion_snapshot,
        cantidad=p.cantidad,
        estado=p.estado,
        pedido_nuevo_id=p.pedido_nuevo_id,
        usuario_id=p.usuario_id,
        creado_en=p.creado_en,
        minutos_espera=minutos_espera(p.creado_en),
        asignado_en=p.asignado_en,
        descartado_en=p.descartado_en,
        motivo_descarte=p.motivo_descarte,
    )


def cancelar_pedido(
    db: Session,
    pedido: Pedido,
    motivo: str,
    admin: Usuario,
) -> tuple[Pedido, list[Preparado]]:
    """Regla de cancelación (Documento Maestro, Sección 6.1 y 8):
    1. Solo admin autoriza y registra la cancelación con motivo obligatorio.
    2. El ancla es PRODUCIDO o NO PRODUCIDO (preparado_en en cocina):
       - Si fue producido: insumos SE MANTIENEN descontados (ya se consumieron),
         y sus líneas pasan a PREPARADOS (DISPONIBLE) para reventa.
       - Si NO fue producido: no se descuenta inventario (nunca se gastó).
       - Si la línea era un preparado previamente asignado: vuelve a DISPONIBLE (Regla 5).
    3. Si hubo pago: el dinero se devuelve en caja (SALIDA DEVOLUCION).
    4. La mesa se libera si no hay otros pedidos abiertos en ella.
    5. Nada se borra: historial_accion inmutable.
    """
    if admin.rol.nombre != "admin":
        raise ValueError("Solo admin puede cancelar pedidos")
    if pedido.estado == "CANCELADO":
        raise ValueError("El pedido ya está cancelado")
    if pedido.estado == "CERRADO":
        raise ValueError("No se puede cancelar un pedido cerrado")

    pedido.estado = "CANCELADO"
    pedido.cancelado_en = func.now()
    pedido.motivo_cancelacion = motivo

    # Liberar mesa si no tiene otros pedidos activos
    if pedido.canal == "MESA" and pedido.mesa_id:
        otro_abierto = (
            db.query(Pedido.id)
            .filter(
                Pedido.mesa_id == pedido.mesa_id,
                Pedido.id != pedido.id,
                Pedido.estado.notin_(("PAGADO", "CERRADO", "CANCELADO")),
            )
            .first()
        )
        if not otro_abierto and pedido.mesa:
            pedido.mesa.estado = "DISPONIBLE"

    preparados_creados: list[Preparado] = []

    for d in pedido.detalles:
        if d.estado != "CANCELADO":
            if d.estado not in ("LISTO", "ENTREGADO"):
                d.estado = "CANCELADO"
            d.cancelado_en = func.now()

        # ¿Esta línea era un preparado reutilizado de un pedido anterior?
        prep_asignado = None
        if d.variacion_snapshot and d.variacion_snapshot.get("preparado_id"):
            prep_asignado = db.get(Preparado, d.variacion_snapshot["preparado_id"])
        if not prep_asignado:
            prep_asignado = (
                db.query(Preparado)
                .filter(
                    Preparado.pedido_nuevo_id == pedido.id,
                    Preparado.producto_id == d.producto_id,
                    Preparado.estado == "ASIGNADO",
                )
                .first()
            )

        if prep_asignado and prep_asignado.estado == "ASIGNADO":
            # Regla 5: Vuelve a DISPONIBLE en la bolsa (no se duplica ni se descuenta de nuevo)
            prep_asignado.estado = "DISPONIBLE"
            prep_asignado.pedido_nuevo_id = None
            prep_asignado.asignado_en = None
            preparados_creados.append(prep_asignado)
        elif d.preparado_en is not None:
            # Producido en cocina: insumos ya se gastaron -> pasa a bolsa de preparados
            # Si cantidad es un entero N, creamos N unidades reusables
            snap = dict(d.variacion_snapshot or {})
            snap.pop("es_preparado", None)
            snap.pop("preparado_id", None)
            cant_unidades = int(d.cantidad) if d.cantidad == int(d.cantidad) else 1
            for _ in range(cant_unidades):
                nuevo_prep = Preparado(
                    producto_id=d.producto_id,
                    pedido_origen_id=pedido.id,
                    detalle_origen_id=d.id,
                    variacion_snapshot=snap if snap else None,
                    cantidad=Decimal("1.00"),
                    estado="DISPONIBLE",
                    pedido_nuevo_id=None,
                    usuario_id=admin.id,
                    creado_en=func.now(),
                )
                db.add(nuevo_prep)
                preparados_creados.append(nuevo_prep)
        else:
            # No producido: nunca se gastó stock, no va a preparados
            pass

    # Manejo de dinero si hubo cobro
    pagos_devueltos = 0
    abierto = turno_abierto(db)
    for p in pedido.pagos:
        if p.estado == "VALIDO":
            p.estado = "DEVUELTO"
            p.devuelto_por = admin.id
            p.devuelto_en = func.now()
            p.motivo_devolucion = f"Cancelación pedido #{pedido.consecutivo}: {motivo}"
            db.add(
                MovimientoCaja(
                    usuario_id=admin.id,
                    tipo="SALIDA",
                    categoria="DEVOLUCION",
                    concepto=f"Devolución cancelación pedido #{pedido.consecutivo}",
                    descripcion=f"Devolución por cancelación pedido #{pedido.consecutivo}: {motivo}",
                    valor=_monto(p.monto),
                    pedido_id=pedido.id,
                    cierre_id=abierto.id if abierto else None,
                )
            )
            pagos_devueltos += 1

    if pagos_devueltos > 0:
        pedido.pagado_en = None

    registrar(
        db,
        admin,
        "CANCELAR_PEDIDO",
        "pedido",
        pedido.id,
        f"consecutivo={pedido.consecutivo} motivo={motivo} preparados={len(preparados_creados)} devoluciones={pagos_devueltos}",
    )

    db.commit()
    db.refresh(pedido)
    for p in preparados_creados:
        db.refresh(p)

    return pedido, preparados_creados


def asignar_preparado(
    db: Session,
    preparado_id: int,
    pedido_id: int,
    usuario: Usuario,
) -> tuple[Preparado, Pedido]:
    """Mesero o caja reutiliza un preparado caliente libre (Reglas Sección 8):
    - Concurrencia segura: SELECT ... FOR UPDATE en la misma transacción.
    - Se marca ASIGNADO inmediatamente.
    - Se agrega como línea al pedido sin generar descuento nuevo de inventario.
    - Se cobra al cliente a precio normal al momento de pagar.
    """
    preparado = (
        db.query(Preparado)
        .with_for_update()
        .filter(Preparado.id == preparado_id)
        .first()
    )
    if not preparado:
        raise ValueError("Preparado no encontrado")
    if preparado.estado != "DISPONIBLE":
        raise ValueError("El preparado ya no está disponible (ya fue asignado o descartado)")

    pedido = (
        db.query(Pedido)
        .options(joinedload(Pedido.detalles), joinedload(Pedido.mesa))
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise ValueError("Pedido no encontrado")
    if pedido.estado in ("CANCELADO", "CERRADO"):
        raise ValueError(f"No se puede agregar un preparado a un pedido {pedido.estado}")
    if pedido.pagado_en is not None:
        raise ValueError("El pedido ya fue cobrado; no admite más productos")

    preparado.estado = "ASIGNADO"
    preparado.pedido_nuevo_id = pedido.id
    preparado.asignado_en = func.now()
    preparado.usuario_id = usuario.id

    producto = preparado.producto or db.get(Producto, preparado.producto_id)
    snapshot = dict(preparado.variacion_snapshot or {})
    snapshot["es_preparado"] = True
    snapshot["preparado_id"] = preparado.id

    ronda = max((d.ronda for d in pedido.detalles), default=1)
    detalle = DetallePedido(
        pedido_id=pedido.id,
        ronda=ronda,
        producto_id=preparado.producto_id,
        cantidad=preparado.cantidad,
        precio_unitario=producto.precio,
        variacion_snapshot=snapshot,
        estado="ENVIADO",
        preparado_en=None,
    )
    db.add(detalle)
    db.flush()

    nota_prep = f"USAR PREPARADO ({int(preparado.cantidad)}x {producto.nombre})"
    if pedido.nota_interna:
        if nota_prep not in pedido.nota_interna:
            pedido.nota_interna += f" | {nota_prep}"
    else:
        pedido.nota_interna = nota_prep

    totales = calcular_totales(db, pedido.detalles + [detalle])
    pedido.subtotal, pedido.iva, pedido.total = totales["subtotal"], totales["iva"], totales["total"]

    if pedido.estado in ("FINALIZADO", "ENTREGADO"):
        pedido.estado = "ENVIADO_A_COCINA"
        pedido.enviado_en = func.now()

    registrar(
        db,
        usuario,
        "ASIGNAR_PREPARADO",
        "preparado",
        preparado.id,
        f"pedido={pedido.consecutivo} producto={producto.nombre}",
    )

    db.commit()
    db.refresh(preparado)
    db.refresh(pedido)
    return preparado, pedido


def descartar_preparado(
    db: Session,
    preparado_id: int,
    motivo: str | None,
    admin: Usuario,
) -> Preparado:
    """Admin descarta un preparado caliente por exceso de tiempo o merma."""
    preparado = (
        db.query(Preparado)
        .with_for_update()
        .filter(Preparado.id == preparado_id)
        .first()
    )
    if not preparado:
        raise ValueError("Preparado no encontrado")
    if preparado.estado != "DISPONIBLE":
        raise ValueError("Solo se pueden descartar preparados en estado DISPONIBLE")

    preparado.estado = "DESCARTADO"
    preparado.descartado_en = func.now()
    preparado.motivo_descarte = motivo
    preparado.usuario_id = admin.id

    registrar(
        db,
        admin,
        "DESCARTAR_PREPARADO",
        "preparado",
        preparado.id,
        f"producto={preparado.producto.nombre if preparado.producto else preparado.producto_id} motivo={motivo}",
    )

    db.commit()
    db.refresh(preparado)
    return preparado


def sugerir_preparado(
    db: Session,
    producto_id: int,
    variacion: dict | None = None,
) -> Preparado | None:
    """Busca si existe un preparado DISPONIBLE que coincida con el producto y variaciones."""
    q = (
        db.query(Preparado)
        .options(joinedload(Preparado.producto), joinedload(Preparado.pedido_origen))
        .filter(
            Preparado.producto_id == producto_id,
            Preparado.estado == "DISPONIBLE",
        )
        .order_by(Preparado.creado_en.asc())
    )
    preparados = q.all()
    if not preparados:
        return None

    if not variacion:
        sin_var = [p for p in preparados if not p.variacion_snapshot]
        return sin_var[0] if sin_var else preparados[0]

    for p in preparados:
        snap = dict(p.variacion_snapshot or {})
        snap.pop("es_preparado", None)
        snap.pop("preparado_id", None)
        if snap == variacion:
            return p

    return None

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models import Configuracion, DetallePedido, DetalleReceta, MovimientoInventario, Pedido, Usuario


def minutos_cocina(db: Session) -> int:
    """Temporizador por defecto para la cocina (config editable)."""
    cfg = db.get(Configuracion, "minutos_cocina")
    if cfg and cfg.valor:
        try:
            return int(cfg.valor)
        except ValueError:
            pass
    return 28


from app.services.inventario import descontar_insumos_de_producto


def descontar_inventario(db: Session, detalle: DetallePedido, cocinero: Usuario) -> None:
    """Cocina ACEPTA el detalle => se descuenta la receta del inventario (regla del dueño).

    - Soporta recetas directas, combos y conversión matemática de unidades.
    - Crea un movimiento por ingrediente con saldos anterior y nuevo.
    - Si el producto es un PREPARADO reutilizado, no se descuenta nada.
    """
    # Preparados reutilizados: la comida ya se cocinó antes y el insumo ya se consumió
    if detalle.variacion_snapshot and (
        detalle.variacion_snapshot.get("es_preparado")
        or detalle.variacion_snapshot.get("preparado_id")
    ):
        return

    referencia = f"Pedido #{detalle.pedido.consecutivo} - {detalle.producto.nombre}"
    descontar_insumos_de_producto(
        db=db,
        producto_id=detalle.producto_id,
        cantidad=detalle.cantidad,
        usuario_id=cocinero.id,
        pedido_id=detalle.pedido_id,
        referencia_base=referencia,
    )


def tiempo_excedido(
    desde: datetime | None, minutos: int
) -> tuple[bool, int]:
    """Devuelve (excedido, segundos_transcurridos) contra el temporizador de cocina."""
    if not desde:
        return False, 0
    if desde.tzinfo is None:
        desde = desde.replace(tzinfo=timezone.utc)
    ahora = datetime.now(timezone.utc)
    segundos = max(0, int((ahora - desde).total_seconds()))
    return segundos > minutos * 60, segundos


def cola_cocina(db: Session):
    """Tickets activos que la cocina debe preparar, agrupados por pedido y ronda.

    La cocina NO ve dinero: solo productos, cantidades, nota y temporizador.
    """
    cfg = db.get(Configuracion, "minutos_cocina")
    minutos = int(cfg.valor) if (cfg and cfg.valor and cfg.valor.isdigit()) else 28

    pedidos = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto),
            joinedload(Pedido.mesa),
        )
        .filter(Pedido.estado.in_(["ENVIADO_A_COCINA", "EN_PREPARACION"]))
        .order_by(Pedido.enviado_en.asc(), Pedido.id.asc())
        .all()
    )

    resultado = []
    for p in pedidos:
        detalles = [d for d in p.detalles if d.estado in ("ENVIADO", "PREPARANDO")]
        if not detalles:
            continue
        excedido, segundos = tiempo_excedido(p.enviado_en, minutos)
        rondas: dict[int, list] = {}
        for d in detalles:
            rondas.setdefault(d.ronda, []).append(d)

        resultado.append(
            {
                "pedido_id": p.id,
                "consecutivo": p.consecutivo,
                "canal": p.canal,
                "mesa_numero": p.mesa.numero if p.mesa else None,
                "cliente": p.cliente,
                "telefono": p.telefono,
                "direccion": p.direccion,
                "nota_interna": p.nota_interna,
                "minutos_temporizador": minutos,
                "tiempo_excedido": excedido,
                "segundos_transcurridos": segundos,
                "rondas": [
                    {
                        "ronda": ronda,
                        "detalles": [
                            {
                                "detalle_id": d.id,
                                "producto_id": d.producto_id,
                                "producto_nombre": d.producto.nombre,
                                "cantidad": d.cantidad,
                                "variacion_snapshot": d.variacion_snapshot,
                                "estado": d.estado,
                                "preparado_en": d.preparado_en,
                                "listo_en": d.listo_en,
                            }
                            for d in sorted(lista, key=lambda x: x.id)
                        ],
                    }
                    for ronda, lista in sorted(rondas.items())
                ],
            }
        )
    return resultado
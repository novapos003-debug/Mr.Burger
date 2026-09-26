from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.tiempo import fecha_local
from app.models import Configuracion, DetallePedido, Pedido, Producto


def siguiente_consecutivo(db: Session, dia: date | None = None) -> int:
    """Numeración de ticket por día (requisito del cliente): reinicia cada día."""
    dia = dia or fecha_local()
    maximo = (
        db.query(func.max(Pedido.consecutivo))
        .filter(Pedido.fecha_dia == dia)
        .scalar()
    )
    return (int(maximo) + 1) if maximo else 1


def porcentaje_iva(db: Session) -> Decimal:
    fila = db.get(Configuracion, "iva_porcentaje")
    if not fila or not fila.valor:
        return Decimal("19")
    try:
        return Decimal(fila.valor)
    except Exception:
        return Decimal("19")


def calcular_totales(db: Session, detalles: list[DetallePedido]) -> dict[str, Decimal]:
    """Subtotal + IVA = Total (guía del cliente).

    El IVA es configurable y respeta el flag `iva_incluido` de cada producto:
    - iva_incluido = TRUE  -> el precio ya trae el IVA (caso normal): total = precio.
    - iva_incluido = FALSE -> el IVA se suma al precio: total = precio * (1 + iva).

    subtotal = base sin IVA; iva = total - subtotal -> identidad contable exacta.
    """
    iva_pct = porcentaje_iva(db)
    factor = Decimal("1") + iva_pct / Decimal("100")

    ids = {d.producto_id for d in detalles}
    incluido = (
        {p.id: p.iva_incluido for p in db.query(Producto.id, Producto.iva_incluido).filter(Producto.id.in_(ids)).all()}
        if ids
        else {}
    )

    total = Decimal("0")
    subtotal = Decimal("0")
    for d in detalles:
        bruto = d.precio_unitario * d.cantidad
        if incluido.get(d.producto_id, True):
            total += bruto
            subtotal += bruto / factor
        else:
            subtotal += bruto
            total += bruto * factor

    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    iva = (total - subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"subtotal": subtotal, "iva": iva, "total": total}
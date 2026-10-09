from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Configuracion, Ingrediente, Producto
from app.services.inventario import expandir_insumos_producto


def disponibilidad_producto(db: Session, producto: Producto) -> tuple[bool, str | None]:
    """Regla del cliente:
    - manual_disponible TRUE/FALSE => decisión forzada del admin.
    - manual_disponible NULL => automático: necesita receta y stock suficiente.
    - Producto SIN receta ni componentes (bebidas sin control etc.) => siempre disponible.
    - Si politica_stock_insuficiente == 'ADVERTIR_Y_PERMITIR', no bloquea ventas.
    """
    if producto.manual_disponible is not None:
        return producto.manual_disponible, (
            "Forzado por administrador" if producto.manual_disponible else "Desactivado por administrador"
        )

    cfg = db.get(Configuracion, "politica_stock_insuficiente")
    politica = cfg.valor.strip().upper() if cfg and cfg.valor else "ADVERTIR_Y_PERMITIR"
    if politica == "ADVERTIR_Y_PERMITIR":
        return True, None

    insumos = expandir_insumos_producto(db, producto.id, Decimal("1"))
    if not insumos:
        return True, None

    for ing_id, info in insumos.items():
        ing = db.get(Ingrediente, ing_id)
        if ing and (ing.stock_actual is None or ing.stock_actual < info["cantidad_base"]):
            return False, f"Falta ingrediente: {info['nombre']}"
    return True, None


def verificar_lineas(db: Session, lineas) -> None:
    """Valida que las líneas de un pedido/ronda se puedan producir.

    Considera la cantidad pedida (no solo una unidad) y suma el consumo de un
    mismo ingrediente cuando aparece en varios productos, convirtiendo unidades
    y resolviendo combos. Lanza ValueError con el primer faltante para que el router
    responda 409 (regla: si un insumo no alcanza, el producto NO está disponible).
    Si politica_stock_insuficiente == 'ADVERTIR_Y_PERMITIR', no bloquea la comanda.
    """
    if not lineas:
        return

    cfg = db.get(Configuracion, "politica_stock_insuficiente")
    politica = cfg.valor.strip().upper() if cfg and cfg.valor else "ADVERTIR_Y_PERMITIR"
    if politica == "ADVERTIR_Y_PERMITIR":
        return

    ids = {l.producto_id for l in lineas}
    productos = {p.id: p for p in db.query(Producto).filter(Producto.id.in_(ids)).all()}

    requerido: dict[int, Decimal] = {}
    origen: dict[int, str] = {}
    for l in lineas:
        if getattr(l, "preparado_id", None) or (
            hasattr(l, "variacion_snapshot")
            and l.variacion_snapshot
            and (l.variacion_snapshot.get("es_preparado") or l.variacion_snapshot.get("preparado_id"))
        ):
            continue  # Viene de un preparado disponible: ya está cocinado, no consume stock

        prod = productos.get(l.producto_id)
        if prod is None:
            raise ValueError(f"Producto {l.producto_id} no existe")
        if prod.manual_disponible is False:
            raise ValueError(f"No disponible: {prod.nombre} (desactivado por administrador)")
        if prod.manual_disponible is True:
            continue  # forzado por el admin: se produce aunque no haya stock

        insumos = expandir_insumos_producto(db, prod.id, l.cantidad)
        for ing_id, info in insumos.items():
            requerido[ing_id] = requerido.get(ing_id, Decimal("0")) + info["cantidad_base"]
            origen.setdefault(ing_id, prod.nombre)

    if not requerido:
        return

    ings = {i.id: i for i in db.query(Ingrediente).filter(Ingrediente.id.in_(requerido)).all()}
    for ing_id, cantidad in requerido.items():
        ing = ings.get(ing_id)
        if ing is None:
            continue
        if ing.stock_actual is None or ing.stock_actual < cantidad:
            raise ValueError(f"No disponible: {origen[ing_id]} (falta {ing.nombre})")


def disponibilidad_masiva(db: Session, productos: list[Producto]) -> dict[int, tuple[bool, str | None]]:
    """Calcula disponibilidad para una lista de productos considerando unidades y combos."""
    resultado: dict[int, tuple[bool, str | None]] = {}
    if not productos:
        return resultado

    cfg = db.get(Configuracion, "politica_stock_insuficiente")
    politica = cfg.valor.strip().upper() if cfg and cfg.valor else "ADVERTIR_Y_PERMITIR"
    if politica == "ADVERTIR_Y_PERMITIR":
        for p in productos:
            if p.manual_disponible is not None:
                resultado[p.id] = (
                    p.manual_disponible,
                    "Forzado por administrador" if p.manual_disponible else "Desactivado por administrador",
                )
            else:
                resultado[p.id] = (True, None)
        return resultado

    productos_map = {p.id: p for p in productos}
    for p in productos:
        if p.manual_disponible is not None:
            resultado[p.id] = (
                p.manual_disponible,
                "Forzado por administrador" if p.manual_disponible else "Desactivado por administrador",
            )
            continue

        insumos = expandir_insumos_producto(db, p.id, Decimal("1"), productos_map=productos_map)
        if not insumos:
            resultado[p.id] = (True, None)
            continue

        faltante = None
        for ing_id, info in insumos.items():
            ing = info.get("ingrediente") or db.get(Ingrediente, ing_id)
            stock = ing.stock_actual if (ing and ing.stock_actual is not None) else Decimal("0")
            if stock < info["cantidad_base"]:
                faltante = info["nombre"]
                break

        resultado[p.id] = (True, None) if faltante is None else (False, f"Falta ingrediente: {faltante}")

    return resultado
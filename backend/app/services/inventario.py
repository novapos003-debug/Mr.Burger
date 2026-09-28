from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.core.unidades import convertir_unidad, normalizar_clave
from app.models import (
    ComponenteCombo,
    Configuracion,
    DetallePedido,
    DetalleReceta,
    Ingrediente,
    MovimientoInventario,
    Producto,
    Usuario,
)


def expandir_insumos_producto(
    db: Session,
    producto_id: int,
    cantidad_producto: Decimal = Decimal("1"),
    visitados: set[int] | None = None,
) -> dict[int, dict[str, Any]]:
    """Expande recursivamente todos los insumos necesarios para producir `cantidad_producto`
    de un producto dado.

    Maneja:
    1. Recetas directas (DetalleReceta).
    2. Productos compuestos / Combos (ComponenteCombo): expande los ingredientes de cada subproducto.
    3. Conversión de unidades automática (ej: 0.07 kg -> 70 g).

    Retorna un diccionario agrupado por `ingrediente_id`:
    {
        ingrediente_id: {
            "ingrediente": Ingrediente,
            "nombre": str,
            "cantidad_base": Decimal,
            "unidad_base": str,
            "costo_unitario": Decimal,
            "costo_total": Decimal,
        }
    }
    """
    if visitados is None:
        visitados = set()

    if producto_id in visitados:
        # Prevenir ciclos infinitos si hubiera referencia circular
        return {}
    visitados.add(producto_id)

    producto = (
        db.query(Producto)
        .options(
            joinedload(Producto.receta).joinedload(DetalleReceta.ingrediente),
            joinedload(Producto.componentes_combo).joinedload(ComponenteCombo.producto_hijo),
        )
        .filter(Producto.id == producto_id)
        .first()
    )
    if not producto:
        return {}

    insumos_agrupados: dict[int, dict[str, Any]] = {}

    # Caso A: Es un COMBO / Producto Compuesto
    if producto.componentes_combo:
        for comp in producto.componentes_combo:
            cant_hijo = comp.cantidad * cantidad_producto
            sub_insumos = expandir_insumos_producto(
                db, comp.producto_hijo_id, cant_hijo, visitados.copy()
            )
            for ing_id, datos in sub_insumos.items():
                if ing_id not in insumos_agrupados:
                    insumos_agrupados[ing_id] = datos
                else:
                    insumos_agrupados[ing_id]["cantidad_base"] += datos["cantidad_base"]
                    insumos_agrupados[ing_id]["costo_total"] += datos["costo_total"]

    # Caso B: Receta directa
    if producto.receta:
        for linea in producto.receta:
            ing = linea.ingrediente
            if not ing:
                continue

            # Convertir la unidad expresada en la receta a la unidad base del insumo
            # Ej: linea.cantidad = 70, linea.unidad = 'g', ing.unidad_base = 'GRAMO'
            cant_en_base = convertir_unidad(
                cantidad=linea.cantidad,
                unidad_origen=linea.unidad,
                unidad_destino=ing.unidad_base,
            )
            cant_total_linea = (cant_en_base * cantidad_producto).quantize(Decimal("0.0001"))
            costo_linea = (cant_total_linea * (ing.costo_unitario or Decimal("0"))).quantize(Decimal("0.01"))

            if ing.id not in insumos_agrupados:
                insumos_agrupados[ing.id] = {
                    "ingrediente": ing,
                    "nombre": ing.nombre,
                    "cantidad_base": cant_total_linea,
                    "unidad_base": ing.unidad_base,
                    "costo_unitario": ing.costo_unitario or Decimal("0"),
                    "costo_total": costo_linea,
                }
            else:
                insumos_agrupados[ing.id]["cantidad_base"] += cant_total_linea
                insumos_agrupados[ing.id]["costo_total"] += costo_linea

    return insumos_agrupados


def calcular_costo_y_margen(db: Session, producto: Producto) -> dict[str, Decimal]:
    """Calcula el costo de producción, utilidad bruta y margen porcentual de un producto
    con base en su receta oficial de 1 unidad.
    """
    insumos = expandir_insumos_producto(db, producto.id, Decimal("1"))
    costo_produccion = sum((d["costo_total"] for d in insumos.values()), Decimal("0")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    precio_venta = Decimal(str(producto.precio or 0)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    utilidad_bruta = (precio_venta - costo_produccion).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    margen_porcentaje = Decimal("0")
    if precio_venta > Decimal("0"):
        margen_porcentaje = ((utilidad_bruta / precio_venta) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    return {
        "costo_produccion": costo_produccion,
        "precio_venta": precio_venta,
        "utilidad_bruta": utilidad_bruta,
        "margen_porcentaje": margen_porcentaje,
    }


def descontar_insumos_de_producto(
    db: Session,
    producto_id: int,
    cantidad: Decimal,
    usuario_id: int,
    pedido_id: int | None = None,
    referencia_base: str = "",
) -> list[MovimientoInventario]:
    """Descuenta atómicamente del inventario los insumos requeridos para producir
    `cantidad` del producto `producto_id`, dejando saldo anterior, saldo nuevo
    y el movimiento de auditoría correspondiente.
    """
    if cantidad <= Decimal("0"):
        return []

    insumos = expandir_insumos_producto(db, producto_id, cantidad)
    if not insumos:
        return []

    movimientos: list[MovimientoInventario] = []

    # Bloquear con FOR UPDATE en orden determinista para concurrencia segura y evitar deadlocks
    ing_ids = sorted(insumos.keys())
    ings_db = (
        db.query(Ingrediente)
        .with_for_update()
        .filter(Ingrediente.id.in_(ing_ids))
        .all()
    )
    mapa_ings = {i.id: i for i in ings_db}

    cfg = db.get(Configuracion, "politica_stock_insuficiente")
    politica = cfg.valor.strip().upper() if cfg and cfg.valor else "BLOQUEAR"

    for ing_id in ing_ids:
        info = insumos[ing_id]
        ing = mapa_ings.get(ing_id)
        if not ing:
            continue

        cant_consumo = info["cantidad_base"]
        if cant_consumo <= Decimal("0"):
            continue

        saldo_ant = ing.stock_actual or Decimal("0")
        saldo_nuevo = saldo_ant - cant_consumo

        if politica == "BLOQUEAR" and saldo_nuevo < Decimal("0"):
            raise ValueError(
                f"Stock insuficiente para {ing.nombre}: disponible {saldo_ant} {ing.unidad_base}, requerido {cant_consumo} {ing.unidad_base}"
            )

        ing.stock_actual = saldo_nuevo

        costo_unit = ing.costo_unitario or Decimal("0")

        mov = MovimientoInventario(
            ingrediente_id=ing.id,
            pedido_id=pedido_id,
            usuario_id=usuario_id,
            cantidad=-cant_consumo,
            unidad=ing.unidad_base,
            saldo_anterior=saldo_ant,
            saldo_nuevo=saldo_nuevo,
            costo_unitario_momento=costo_unit,
            tipo="VENTA",
            referencia=referencia_base or f"Venta {int(cantidad)}x {info['nombre']}",
        )
        db.add(mov)
        db.flush()
        movimientos.append(mov)

        # Encolar en registro_sync (Patrón Outbox) para sincronización con la nube
        from app.services.sync import encolar_sync

        encolar_sync(
            db,
            tipo="DESCUENTO_STOCK",
            entidad="movimiento_inventario",
            payload={
                "id": mov.id,
                "ingrediente_id": ing.id,
                "ingrediente_nombre": info.get("nombre", ing.nombre),
                "pedido_id": pedido_id,
                "cantidad": float(mov.cantidad),
                "unidad": mov.unidad,
                "saldo_anterior": float(mov.saldo_anterior) if mov.saldo_anterior is not None else None,
                "saldo_nuevo": float(mov.saldo_nuevo) if mov.saldo_nuevo is not None else None,
                "stock_actual_checkpoint": float(ing.stock_actual) if ing.stock_actual is not None else None,
                "tipo": "VENTA",
                "referencia": mov.referencia,
            },
            entidad_id=mov.id,
            dispositivo_id=f"USER_{usuario_id}",
        )

    return movimientos

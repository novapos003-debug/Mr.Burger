from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import admin_required
from app.core.unidades import convertir_unidad
from app.database import get_db, safe_commit
from app.models import (
    CategoriaInsumo,
    ComponenteCombo,
    DetalleReceta,
    Ingrediente,
    MovimientoInventario,
    Producto,
    Usuario,
)
from app.schemas import (
    CategoriaInsumoIn,
    CategoriaInsumoOut,
    ComponenteComboIn,
    ComponenteComboOut,
    DetalleRecetaIn,
    IngredienteIn,
    IngredienteOut,
    IngredienteUpdate,
    MovimientoInventarioOut,
    RecetaOut,
)
from app.services.historial import registrar
from app.services.inventario import calcular_costo_y_margen

router = APIRouter(prefix="/ingredientes", tags=["inventario"])


# ============================================================
# CATEGORÍAS DE INSUMOS
# ============================================================

@router.get("/categorias", response_model=list[CategoriaInsumoOut])
def listar_categorias_insumo(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Lista las categorías disponibles para clasificar insumos/materias primas."""
    return (
        db.query(CategoriaInsumo)
        .filter(CategoriaInsumo.activo.is_(True))
        .order_by(CategoriaInsumo.nombre)
        .all()
    )


@router.post("/categorias", response_model=CategoriaInsumoOut, status_code=status.HTTP_201_CREATED)
def crear_categoria_insumo(
    data: CategoriaInsumoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    nombre_limpio = data.nombre.strip().upper()
    if db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == nombre_limpio).first():
        raise HTTPException(status_code=409, detail="Ya existe esa categoría de insumos")

    cat = CategoriaInsumo(nombre=nombre_limpio, descripcion=data.descripcion)
    db.add(cat)
    db.flush()
    registrar(db, usuario, "CREAR_CATEGORIA_INSUMO", "categoria_insumo", cat.id, cat.nombre)
    safe_commit(db)
    db.refresh(cat)
    return cat


# ============================================================
# INGREDIENTES (solo admin: costos, stock y proveedor son sensibles)
# ============================================================

def to_ingrediente_out(ing: Ingrediente) -> IngredienteOut:
    return IngredienteOut(
        id=ing.id,
        categoria_insumo_id=ing.categoria_insumo_id,
        categoria_insumo_nombre=ing.categoria_insumo.nombre if ing.categoria_insumo else None,
        nombre=ing.nombre,
        unidad_base=ing.unidad_base,
        costo_unitario=ing.costo_unitario,
        costo_proveedor=ing.costo_proveedor,
        stock_actual=ing.stock_actual,
        stock_minimo=ing.stock_minimo,
        stock_ideal=ing.stock_ideal,
        proveedor_id=ing.proveedor_id,
        proveedor_nombre=ing.proveedor.nombre if ing.proveedor else None,
        stock_bajo=ing.stock_actual < ing.stock_minimo,
        activo=ing.activo,
    )


@router.get("", response_model=list[IngredienteOut])
def listar_ingredientes(
    categoria_insumo_id: int | None = None,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    q = db.query(Ingrediente).options(
        joinedload(Ingrediente.categoria_insumo),
        joinedload(Ingrediente.proveedor),
    )
    if categoria_insumo_id is not None:
        q = q.filter(Ingrediente.categoria_insumo_id == categoria_insumo_id)
    if not incluir_inactivos:
        q = q.filter(Ingrediente.activo.is_(True))
    return [to_ingrediente_out(i) for i in q.order_by(Ingrediente.nombre).all()]


@router.post("", response_model=IngredienteOut, status_code=status.HTTP_201_CREATED)
def crear_ingrediente(
    data: IngredienteIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    if db.query(Ingrediente).filter(Ingrediente.nombre == data.nombre, Ingrediente.activo.is_(True)).first():
        raise HTTPException(status_code=409, detail="Ya existe ese ingrediente")
    ing = Ingrediente(**data.model_dump())
    db.add(ing)
    db.flush()
    if ing.stock_actual and Decimal(str(ing.stock_actual)) != 0:
        db.add(
            MovimientoInventario(
                ingrediente_id=ing.id,
                usuario_id=usuario.id,
                cantidad=Decimal(str(ing.stock_actual)),
                unidad=ing.unidad_base,
                saldo_anterior=Decimal("0"),
                saldo_nuevo=Decimal(str(ing.stock_actual)),
                costo_unitario_momento=ing.costo_unitario,
                tipo="AJUSTE",
                referencia="Stock inicial al crear el ingrediente",
            )
        )
    registrar(db, usuario, "CREAR_INGREDIENTE", "ingrediente", ing.id, ing.nombre)
    safe_commit(db)
    db.refresh(ing)
    return to_ingrediente_out(ing)


@router.put("/{ingrediente_id}", response_model=IngredienteOut)
def actualizar_ingrediente(
    ingrediente_id: int,
    data: IngredienteUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    ing = db.get(Ingrediente, ingrediente_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")

    cambios = data.model_dump(exclude_unset=True)
    stock_delta: Decimal | None = None
    anterior = Decimal(str(ing.stock_actual or 0))

    if cambios.get("stock_actual") is not None:
        nuevo = Decimal(str(cambios["stock_actual"]))
        stock_delta = nuevo - anterior

    for campo, valor in cambios.items():
        setattr(ing, campo, valor)

    if stock_delta is not None and stock_delta != 0:
        # Regla del cliente: el stock es un historial. Un ajuste manual NO puede
        # pisar el stock sin dejar su movimiento correspondiente.
        db.add(
            MovimientoInventario(
                ingrediente_id=ing.id,
                usuario_id=usuario.id,
                cantidad=stock_delta,
                unidad=ing.unidad_base,
                saldo_anterior=anterior,
                saldo_nuevo=ing.stock_actual,
                costo_unitario_momento=ing.costo_unitario,
                tipo="AJUSTE",
                referencia="Ajuste manual de stock por administrador",
            )
        )
        registrar(
            db, usuario, "AJUSTAR_INVENTARIO", "ingrediente", ing.id,
            f"{ing.nombre}: delta={stock_delta}",
        )
    else:
        registrar(
            db, usuario, "MODIFICAR_INGREDIENTE", "ingrediente", ing.id,
            ", ".join(sorted(cambios.keys())) or None,
        )
    safe_commit(db)
    db.refresh(ing)
    return to_ingrediente_out(ing)


@router.delete("/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_ingrediente(
    ingrediente_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Soft-delete: nada se borra para conservar el historial (requisito del cliente)."""
    ing = db.get(Ingrediente, ingrediente_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    if db.query(DetalleReceta).filter(DetalleReceta.ingrediente_id == ingrediente_id).first():
        raise HTTPException(status_code=409, detail="Este ingrediente está en uso en recetas; no se puede inactivar")
    ing.activo = False
    registrar(db, usuario, "DESACTIVAR_INGREDIENTE", "ingrediente", ing.id, ing.nombre)
    safe_commit(db)


# ============================================================
# KARDEX / MOVIMIENTOS DE INVENTARIO
# ============================================================

@router.get("/{ingrediente_id}/movimientos", response_model=list[MovimientoInventarioOut])
def ver_movimientos_ingrediente(
    ingrediente_id: int,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Historial inmutable (Kardex) de entradas, salidas y ajustes de un insumo."""
    ing = db.get(Ingrediente, ingrediente_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")

    movs = (
        db.query(MovimientoInventario)
        .options(
            joinedload(MovimientoInventario.ingrediente),
        )
        .filter(MovimientoInventario.ingrediente_id == ingrediente_id)
        .order_by(MovimientoInventario.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    salida = []
    for m in movs:
        salida.append(
            MovimientoInventarioOut(
                id=m.id,
                ingrediente_id=m.ingrediente_id,
                ingrediente_nombre=m.ingrediente.nombre if m.ingrediente else None,
                pedido_id=m.pedido_id,
                compra_id=m.compra_id,
                usuario_id=m.usuario_id,
                cantidad=m.cantidad,
                unidad=m.unidad or (m.ingrediente.unidad_base if m.ingrediente else "u"),
                saldo_anterior=m.saldo_anterior,
                saldo_nuevo=m.saldo_nuevo,
                costo_unitario_momento=m.costo_unitario_momento,
                tipo=m.tipo,
                referencia=m.referencia,
                creado_en=m.creado_en,
            )
        )
    return salida


# ============================================================
# RECETAS & ANÁLISIS DE COSTO
# ============================================================

@router.get("/productos/{producto_id}/receta", response_model=list[RecetaOut])
def ver_receta(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    resultado = []
    for linea in prod.receta:
        ing = linea.ingrediente
        costo_u = ing.costo_unitario if ing else Decimal("0")
        try:
            cant_base = convertir_unidad(linea.cantidad, linea.unidad, ing.unidad_base)
        except Exception:
            cant_base = linea.cantidad
        costo_linea = (cant_base * costo_u).quantize(Decimal("0.01"))

        resultado.append(
            RecetaOut(
                ingrediente_id=linea.ingrediente_id,
                ingrediente_nombre=linea.ingrediente.nombre,
                cantidad=linea.cantidad,
                unidad=linea.unidad,
                unidad_base=linea.ingrediente.unidad_base,
                costo_unitario=costo_u,
                costo_total=costo_linea,
            )
        )
    return resultado


@router.put("/productos/{producto_id}/receta", response_model=list[RecetaOut])
def reemplazar_receta(
    producto_id: int,
    lineas: list[DetalleRecetaIn],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Reemplaza la receta completa del producto (con fracciones y conversión de unidades).
    Si se manda lista vacía, el producto queda sin receta => siempre disponible."""
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    ids = [l.ingrediente_id for l in lineas]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Un ingrediente repetido en la receta")

    for l in lineas:
        ing = db.get(Ingrediente, l.ingrediente_id)
        if not ing:
            raise HTTPException(status_code=404, detail=f"Ingrediente {l.ingrediente_id} no existe")
        # Validar compatibilidad de unidades
        try:
            convertir_unidad(l.cantidad, l.unidad, ing.unidad_base)
        except ValueError as err:
            raise HTTPException(
                status_code=422,
                detail=f"Error en {ing.nombre}: {str(err)}",
            )

    db.query(DetalleReceta).filter(DetalleReceta.product_id == producto_id).delete()
    for l in lineas:
        db.add(DetalleReceta(product_id=producto_id, ingrediente_id=l.ingrediente_id, cantidad=l.cantidad, unidad=l.unidad))
    registrar(
        db, usuario, "MODIFICAR_RECETA", "producto", producto_id,
        f"lineas={len(lineas)}",
    )
    safe_commit(db)
    return ver_receta(producto_id, db=db, _=None)


@router.get("/productos/{producto_id}/costo-utilidad")
def ver_costo_utilidad(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Calcula y retorna costo de insumos, utilidad bruta y margen porcentual del producto."""
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return calcular_costo_y_margen(db, prod)


# ============================================================
# COMBOS / PRODUCTOS COMPUESTOS
# ============================================================

@router.get("/combos/{producto_id}/componentes", response_model=list[ComponenteComboOut])
def ver_componentes_combo(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return [
        ComponenteComboOut(
            id=c.id,
            producto_hijo_id=c.producto_hijo_id,
            producto_hijo_nombre=c.producto_hijo.nombre,
            cantidad=c.cantidad,
            precio_unitario=c.producto_hijo.precio,
        )
        for c in prod.componentes_combo
    ]


@router.put("/combos/{producto_id}/componentes", response_model=list[ComponenteComboOut])
def configurar_componentes_combo(
    producto_id: int,
    componentes: list[ComponenteComboIn],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Configura los subproductos que componen un Combo."""
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    hijo_ids = [c.producto_hijo_id for c in componentes]
    if producto_id in hijo_ids:
        raise HTTPException(status_code=422, detail="Un combo no puede contenerse a sí mismo")
    if len(hijo_ids) != len(set(hijo_ids)):
        raise HTTPException(status_code=422, detail="Producto repetido en la lista de componentes")

    for c in componentes:
        hijo = db.get(Producto, c.producto_hijo_id)
        if not hijo or not hijo.activo:
            raise HTTPException(status_code=404, detail=f"Producto {c.producto_hijo_id} no existe o inactivo")

    db.query(ComponenteCombo).filter(ComponenteCombo.combo_producto_id == producto_id).delete()
    for c in componentes:
        db.add(ComponenteCombo(combo_producto_id=producto_id, producto_hijo_id=c.producto_hijo_id, cantidad=c.cantidad))

    registrar(
        db, usuario, "MODIFICAR_COMBO", "producto", producto_id,
        f"componentes={len(componentes)}",
    )
    safe_commit(db)
    return ver_componentes_combo(producto_id, db=db, _=None)


# Alias bajo /inventario para compatibilidad total
combo_alias_router = APIRouter(prefix="/inventario", tags=["inventario"])

@combo_alias_router.get("/combos/{producto_id}/componentes", response_model=list[ComponenteComboOut])
def ver_componentes_combo_alias(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    return ver_componentes_combo(producto_id, db=db, _=_)


@combo_alias_router.put("/combos/{producto_id}/componentes", response_model=list[ComponenteComboOut])
def configurar_componentes_combo_alias(
    producto_id: int,
    componentes: list[ComponenteComboIn],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    return configurar_componentes_combo(producto_id, componentes=componentes, db=db, usuario=usuario)
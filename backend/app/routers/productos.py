import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.deps import admin_required, staff_required
from app.database import get_db, safe_commit
from app.models import Categoria, ComponenteCombo, Configuracion, DetalleReceta, Producto, Usuario
from app.schemas import (
    ComponenteComboOut,
    ProductoDisponibilidadUpdate,
    ProductoIn,
    ProductoOut,
    ProductoUpdate,
)
from app.services.disponibilidad import disponibilidad_masiva, disponibilidad_producto
from app.services.historial import registrar
from app.services.inventario import calcular_costo_y_margen

router = APIRouter(prefix="/productos", tags=["catálogo"])

VIDEN_PRECIO = {"admin", "cajero", "mesero"}


def producto_out(
    prod: Producto,
    disponible: bool,
    db: Session | None = None,
    es_admin: bool = False,
    incluir_finanzas: bool = False,
) -> ProductoOut:
    es_cocina = True
    if prod.categoria:
        if prod.categoria.tipo:
            es_cocina = (prod.categoria.tipo.nombre == "COMIDA")
        elif prod.categoria.tipo_id:
            es_cocina = (prod.categoria.tipo_id == 1)
        if "BEBIDA" in (prod.categoria.nombre or "").upper():
            es_cocina = False

    ingredientes = []
    if prod.receta:
        ingredientes = [
            linea.ingrediente.nombre
            for linea in prod.receta
            if linea.ingrediente and linea.ingrediente.nombre
        ]

    costo_produccion = None
    utilidad_bruta = None
    margen_porcentaje = None
    if incluir_finanzas and es_admin and db is not None:
        try:
            finanzas = calcular_costo_y_margen(db, prod)
            costo_produccion = finanzas["costo_produccion"]
            utilidad_bruta = finanzas["utilidad_bruta"]
            margen_porcentaje = finanzas["margen_porcentaje"]
        except Exception:
            pass

    componentes_combo = []
    if prod.componentes_combo:
        for c in prod.componentes_combo:
            if c.producto_hijo:
                componentes_combo.append(
                    ComponenteComboOut(
                        id=c.id,
                        producto_hijo_id=c.producto_hijo_id,
                        producto_hijo_nombre=c.producto_hijo.nombre,
                        cantidad=c.cantidad,
                        precio_unitario=c.producto_hijo.precio,
                    )
                )

    permite_adiciones = getattr(prod, "permite_adiciones", True)
    if permite_adiciones is None:
        permite_adiciones = False if not es_cocina else True

    return ProductoOut(
        id=prod.id,
        categoria_id=prod.categoria_id,
        nombre=prod.nombre,
        descripcion=prod.descripcion,
        imagen_url=prod.imagen_url,
        precio=prod.precio,
        iva_incluido=prod.iva_incluido,
        empaque_llevar_id=prod.empaque_llevar_id,
        permite_adiciones=permite_adiciones,
        disponible=disponible,
        activo=prod.activo,
        es_cocina=es_cocina,
        ingredientes_receta=ingredientes,
        costo_produccion=costo_produccion,
        utilidad_bruta=utilidad_bruta,
        margen_porcentaje=margen_porcentaje,
        es_combo=bool(prod.componentes_combo),
        componentes_combo=componentes_combo,
    )


@router.get("", response_model=list[ProductoOut])
def listar_productos(
    categoria_id: int | None = None,
    solo_disponibles: bool = False,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    """Lista el catálogo para el dispositivo. Reglas del cliente:
    - Mesero y cocina NO ven precios (campo precio llega como null).
    - Mesero ve disponibilidad (agotado / quedan pocos) para orientar al cliente.
    """
    q = db.query(Producto).options(
        joinedload(Producto.categoria).joinedload(Categoria.tipo),
        joinedload(Producto.receta).joinedload(DetalleReceta.ingrediente),
        joinedload(Producto.componentes_combo).joinedload(ComponenteCombo.producto_hijo),
    )
    if categoria_id is not None:
        q = q.filter(Producto.categoria_id == categoria_id)
    elif usuario.rol.nombre in ("mesero", "cocina"):
        # Ocultar empaques desechables o servicios internos de la carta de comida del mesero
        q = q.filter(Producto.categoria_id != 99)
    if not incluir_inactivos:
        q = q.filter(Producto.activo.is_(True))
    productos = q.order_by(Producto.nombre).all()

    quita_precio = usuario.rol.nombre not in VIDEN_PRECIO
    es_admin = usuario.rol.nombre == "admin"
    mapa = disponibilidad_masiva(db, productos)

    salida = []
    for p in productos:
        disponible = mapa[p.id][0]
        if solo_disponibles and not disponible:
            continue
        item = producto_out(p, disponible, db=db, es_admin=es_admin)
        if quita_precio:
            item.precio = None
        salida.append(item)
    return salida


class AdicionItem(BaseModel):
    id: str
    nombre: str
    precio: float
    activo: bool = True


ADICIONES_DEFAULT = [
    {"id": "ad-tocineta", "nombre": "Tocineta Ahumada", "precio": 3000, "activo": True},
    {"id": "ad-cheddar", "nombre": "Doble Queso Cheddar", "precio": 2500, "activo": True},
    {"id": "ad-carne", "nombre": "Carne Extra 125g", "precio": 5000, "activo": True},
    {"id": "ad-huevo", "nombre": "Huevo Frito", "precio": 2000, "activo": True},
    {"id": "ad-cebolla-caram", "nombre": "Cebolla Caramelizada", "precio": 1500, "activo": True},
    {"id": "ad-costeno", "nombre": "Queso Costeño Rallado", "precio": 2000, "activo": True},
    {"id": "ad-papas", "nombre": "Porción Papas Extra", "precio": 4000, "activo": True},
]


@router.get("/adiciones/configuracion", response_model=list[AdicionItem])
def listar_adiciones_configuracion(
    db: Session = Depends(get_db),
    _: Usuario = Depends(staff_required),
):
    """Retorna las adiciones configuradas para comanda y meseros."""
    cfg = db.get(Configuracion, "adiciones_disponibles")
    if not cfg or not cfg.valor:
        return ADICIONES_DEFAULT
    try:
        data = json.loads(cfg.valor)
        return data
    except Exception:
        return ADICIONES_DEFAULT


@router.put("/adiciones/configuracion", response_model=list[AdicionItem])
def guardar_adiciones_configuracion(
    adiciones: list[AdicionItem],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Permite al admin configurar qué adiciones aparecen, sus precios y estado activo/inactivo."""
    cfg = db.get(Configuracion, "adiciones_disponibles")
    data_dict = [a.model_dump() for a in adiciones]
    valor_json = json.dumps(data_dict, ensure_ascii=False)
    if not cfg:
        cfg = Configuracion(
            clave="adiciones_disponibles",
            valor=valor_json,
            descripcion="Catálogo de adiciones extra con costo disponibles en comanda",
        )
        db.add(cfg)
    else:
        cfg.valor = valor_json
    registrar(db, usuario, "MODIFICAR_ADICIONES", "configuracion", None, f"total={len(adiciones)}")
    safe_commit(db)
    db.refresh(cfg)
    return adiciones


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    prod = (
        db.query(Producto)
        .options(
            joinedload(Producto.categoria).joinedload(Categoria.tipo),
            joinedload(Producto.receta).joinedload(DetalleReceta.ingrediente),
            joinedload(Producto.componentes_combo).joinedload(ComponenteCombo.producto_hijo),
        )
        .filter(Producto.id == producto_id)
        .first()
    )
    if not prod or not prod.activo:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    disponible, _ = disponibilidad_producto(db, prod)
    es_admin = usuario.rol.nombre == "admin"
    item = producto_out(prod, disponible, db=db, es_admin=es_admin, incluir_finanzas=True)
    if usuario.rol.nombre not in VIDEN_PRECIO:
        item.precio = None
    return item


@router.post("", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def crear_producto(
    data: ProductoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    if not db.get(Categoria, data.categoria_id):
        raise HTTPException(status_code=404, detail="categoria_id no existe")
    prod = Producto(**data.model_dump())
    db.add(prod)
    db.flush()
    registrar(db, usuario, "CREAR_PRODUCTO", "producto", prod.id, f"{prod.nombre} precio={prod.precio}")
    safe_commit(db)
    db.refresh(prod)
    disponible, _ = disponibilidad_producto(db, prod)
    return producto_out(prod, disponible)


@router.put("/{producto_id}", response_model=ProductoOut)
def actualizar_producto(
    producto_id: int,
    data: ProductoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if data.categoria_id is not None and not db.get(Categoria, data.categoria_id):
        raise HTTPException(status_code=404, detail="categoria_id no existe")
    anterior = prod.precio
    cambios = data.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(prod, campo, valor)
    if "precio" in cambios:
        registrar(db, usuario, "MODIFICAR_PRECIO", "producto", prod.id, f"{prod.nombre}: {anterior} -> {prod.precio}")
    else:
        registrar(db, usuario, "MODIFICAR_PRODUCTO", "producto", prod.id, ", ".join(sorted(cambios.keys())) or None)
    safe_commit(db)
    db.refresh(prod)
    disponible, _ = disponibilidad_producto(db, prod)
    return producto_out(prod, disponible)


@router.put("/{producto_id}/disponibilidad", response_model=ProductoOut)
def forzar_disponibilidad(
    producto_id: int,
    data: ProductoDisponibilidadUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Solo el admin puede forzar disponible/no disponible por encima del stock."""
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    prod.manual_disponible = data.manual_disponible
    registrar(
        db, usuario, "FORZAR_DISPONIBILIDAD", "producto", prod.id,
        f"{prod.nombre} -> {data.manual_disponible}",
    )
    safe_commit(db)
    db.refresh(prod)
    disponible, _ = disponibilidad_producto(db, prod)
    return producto_out(prod, disponible)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Soft-delete: nada se borra, solo se desactiva (requisito del cliente)."""
    prod = db.get(Producto, producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    prod.activo = False
    registrar(db, usuario, "DESACTIVAR_PRODUCTO", "producto", prod.id, prod.nombre)
    safe_commit(db)
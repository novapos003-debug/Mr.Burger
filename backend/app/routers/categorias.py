from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import admin_required, staff_required
from app.database import get_db, safe_commit
from app.models import Categoria, TipoCategoria, Usuario
from app.schemas import CategoriaIn, CategoriaOut, CategoriaUpdate, TipoCategoriaOut
from app.services.historial import registrar

router = APIRouter(prefix="/categorias", tags=["catálogo"])


@router.get("/tipos", response_model=list[TipoCategoriaOut])
def listar_tipos(db: Session = Depends(get_db), _: Usuario = Depends(staff_required)):
    return db.query(TipoCategoria).order_by(TipoCategoria.id).all()


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(
    incluir_inactivas: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(staff_required),
):
    q = db.query(Categoria)
    if not incluir_inactivas:
        q = q.filter(Categoria.activo.is_(True))
    if usuario.rol.nombre in ("mesero", "cocina"):
        q = q.filter(Categoria.id != 99)
    return q.order_by(Categoria.orden, Categoria.nombre).all()


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    data: CategoriaIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    if not db.get(TipoCategoria, data.tipo_id):
        raise HTTPException(status_code=404, detail="tipo_id no existe")
    if db.query(Categoria).filter(Categoria.nombre == data.nombre, Categoria.activo.is_(True)).first():
        raise HTTPException(status_code=409, detail="Ya existe una categoría activa con ese nombre")
    cat = Categoria(**data.model_dump())
    db.add(cat)
    db.flush()
    registrar(db, usuario, "CREAR_CATEGORIA", "categoria", cat.id, cat.nombre)
    safe_commit(db)
    db.refresh(cat)
    return cat


@router.put("/{categoria_id}", response_model=CategoriaOut)
def actualizar_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    cat = db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if data.tipo_id is not None and not db.get(TipoCategoria, data.tipo_id):
        raise HTTPException(status_code=404, detail="tipo_id no existe")
    cambios = data.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(cat, campo, valor)
    registrar(db, usuario, "MODIFICAR_CATEGORIA", "categoria", cat.id, ", ".join(sorted(cambios.keys())) or None)
    safe_commit(db)
    db.refresh(cat)
    return cat


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Soft-delete: nada se borra, solo se desactiva (requisito del cliente)."""
    cat = db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    cat.activo = False
    registrar(db, usuario, "DESACTIVAR_CATEGORIA", "categoria", cat.id, cat.nombre)
    safe_commit(db)
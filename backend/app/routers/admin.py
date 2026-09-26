from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import admin_required
from app.database import get_db
from app.models import Usuario
from app.schemas.admin import (
    AlertaStockItem,
    CompraIn,
    CompraOut,
    DashboardOut,
    HistorialAccionOut,
    ReporteVentasOut,
)
from app.services.admin import (
    consultar_auditoria,
    listar_compras,
    obtener_dashboard,
    obtener_stock_critico,
    registrar_compra,
    reporte_ventas,
)
from app.services.historial import registrar

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardOut)
def ver_dashboard(
    fecha: date | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Dashboard gerencial para el iPad/móvil del dueño.
    Muestra KPIs en vivo, ticket promedio, ventas por canal y métodos, alertas de stock."""
    return obtener_dashboard(db, fecha)


@router.get("/reportes/ventas", response_model=ReporteVentasOut)
def ver_reporte_ventas(
    desde: date = Query(...),
    hasta: date = Query(...),
    canal: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Genera reporte histórico de ventas por rango de fechas y canal."""
    if desde > hasta:
        raise HTTPException(status_code=422, detail="La fecha 'desde' no puede ser posterior a 'hasta'")
    return reporte_ventas(db, desde, hasta, canal)


@router.get("/stock-critico", response_model=list[AlertaStockItem])
def ver_stock_critico(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Lista insumos en nivel crítico con déficit y costo estimado para abastecer."""
    return obtener_stock_critico(db)


@router.get("/auditoria", response_model=list[HistorialAccionOut])
def ver_auditoria(
    usuario_id: int | None = None,
    accion: str | None = None,
    entidad: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Consulta paginada del historial inmutable de acciones del sistema."""
    return consultar_auditoria(db, usuario_id, accion, entidad, limit, offset)


@router.post("/compras", response_model=CompraOut, status_code=status.HTTP_201_CREATED)
def crear_compra(
    data: CompraIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Registra una compra de insumos reabasteciendo el inventario."""
    try:
        compra = registrar_compra(db, data, admin)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    compras = listar_compras(db, limit=1, offset=0)
    return next((c for c in compras if c.id == compra.id), None)


@router.get("/compras", response_model=list[CompraOut])
def ver_compras(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Lista el historial de compras a proveedores con sus detalles."""
    return listar_compras(db, limit, offset)


# ============================================================
# CONFIGURACIÓN DEL LOCAL
# ============================================================
from pydantic import BaseModel
from app.models import Configuracion


class ConfiguracionUpdateIn(BaseModel):
    valor: str


@router.get("/configuracion")
def listar_configuracion(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Retorna las configuraciones globales del restaurante."""
    return db.query(Configuracion).all()


@router.put("/configuracion/{clave}")
def actualizar_configuracion(
    clave: str,
    data: ConfiguracionUpdateIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(admin_required),
):
    """Actualiza un parámetro de configuración (ej: politica_stock_insuficiente, iva_porcentaje, minutos_cocina)."""
    cfg = db.get(Configuracion, clave)
    if not cfg:
        cfg = Configuracion(clave=clave, valor=data.valor)
        db.add(cfg)
    else:
        cfg.valor = data.valor
    from app.services.historial import registrar
    registrar(db, usuario, "MODIFICAR_CONFIG", "configuracion", None, f"{clave}={data.valor}")
    db.commit()
    db.refresh(cfg)
    return cfg


# ============================================================
# GESTIÓN DE USUARIOS Y ROLES (ADMINISTRACIÓN)
# ============================================================
from app.models import Rol
from app.core.security import hash_password
from app.schemas.admin import (
    UsuarioAdminOut,
    UsuarioCreateIn,
    UsuarioPasswordUpdateIn,
    UsuarioEstadoUpdateIn,
)


@router.get("/usuarios", response_model=list[UsuarioAdminOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Lista todos los usuarios del sistema ordenados por id."""
    usuarios = db.query(Usuario).order_by(Usuario.id.asc()).all()
    # Filtrar usuarios dummy de auditoría interna
    usuarios_reales = [u for u in usuarios if not u.nombre.startswith("Audit Inactivo")]
    return [
        UsuarioAdminOut(
            id=u.id,
            nombre=u.nombre,
            usuario=u.usuario,
            rol_id=u.rol_id,
            rol=u.rol.nombre if u.rol else "sin_rol",
            activo=u.activo,
            creado_en=u.creado_en,
        )
        for u in usuarios_reales
    ]


@router.post("/usuarios", response_model=UsuarioAdminOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    data: UsuarioCreateIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Crea un nuevo usuario del sistema con su rol y contraseña inicial."""
    clean_user = data.usuario.strip().lower()
    usuario_existente = db.query(Usuario).filter(Usuario.usuario == clean_user).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario '{clean_user}' ya existe. Elige otro.",
        )

    rol = db.query(Rol).filter(Rol.nombre == data.rol.lower()).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol '{data.rol}' no existe.",
        )

    nuevo_u = Usuario(
        nombre=data.nombre.strip(),
        usuario=clean_user,
        rol_id=rol.id,
        password_hash=hash_password(data.password),
        activo=True,
    )
    db.add(nuevo_u)
    db.flush()

    registrar(db, admin, "CREAR_USUARIO", "usuario", nuevo_u.id, f"usuario={nuevo_u.usuario} rol={rol.nombre}")
    db.commit()
    db.refresh(nuevo_u)

    return UsuarioAdminOut(
        id=nuevo_u.id,
        nombre=nuevo_u.nombre,
        usuario=nuevo_u.usuario,
        rol_id=nuevo_u.rol_id,
        rol=rol.nombre,
        activo=nuevo_u.activo,
        creado_en=nuevo_u.creado_en,
    )


@router.put("/usuarios/{usuario_id}/password")
def cambiar_password_usuario(
    usuario_id: int,
    data: UsuarioPasswordUpdateIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Permite al administrador restablecer o cambiar la contraseña de cualquier usuario."""
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    u.password_hash = hash_password(data.nueva_password)
    registrar(db, admin, "MODIFICAR_PASSWORD", "usuario", u.id, f"cambio clave para usuario={u.usuario}")
    db.commit()
    return {"status": "ok", "mensaje": f"Contraseña actualizada para {u.usuario}"}


@router.put("/usuarios/{usuario_id}/estado", response_model=UsuarioAdminOut)
def cambiar_estado_usuario(
    usuario_id: int,
    data: UsuarioEstadoUpdateIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Activa o desactiva a un usuario. Impide desactivarse a sí mismo."""
    if usuario_id == admin.id and not data.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes desactivar tu propia cuenta administradora")

    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    u.activo = data.activo
    accion = "ACTIVAR_USUARIO" if data.activo else "DESACTIVAR_USUARIO"
    registrar(db, admin, accion, "usuario", u.id, f"estado={data.activo}")
    db.commit()
    db.refresh(u)

    return UsuarioAdminOut(
        id=u.id,
        nombre=u.nombre,
        usuario=u.usuario,
        rol_id=u.rol_id,
        rol=u.rol.nombre if u.rol else "sin_rol",
        activo=u.activo,
        creado_en=u.creado_en,
    )


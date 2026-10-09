from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import admin_required, get_current_user
from app.database import get_db, safe_commit
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
    _: Usuario = Depends(get_current_user),
):
    """Retorna las configuraciones globales del restaurante (accesible para mesero, caja, cocina y admin)."""
    return db.query(Configuracion).all()


configuracion_alias_router = APIRouter(tags=["configuracion"])


@configuracion_alias_router.get("/configuracion")
def listar_configuracion_alias(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Alias raíz para consultar configuraciones del restaurante."""
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
    safe_commit(db)
    db.refresh(cfg)
    return cfg


# ============================================================
# GESTIÓN DE USUARIOS Y ROLES (ADMINISTRACIÓN)
# ============================================================
from app.models import Rol
from app.core.security import hash_password, verify_password
from app.schemas.admin import (
    ResetSistemaIn,
    UsuarioAdminOut,
    UsuarioCreateIn,
    UsuarioEstadoUpdateIn,
    UsuarioMarcasUpdateIn,
    UsuarioPasswordUpdateIn,
)


def _usuario_out(u: Usuario) -> UsuarioAdminOut:
    return UsuarioAdminOut(
        id=u.id,
        nombre=u.nombre,
        usuario=u.usuario,
        rol_id=u.rol_id,
        rol=u.rol.nombre if u.rol else "sin_rol",
        activo=u.activo,
        fijado=bool(u.fijado),
        es_demo=bool(u.es_demo),
        creado_en=u.creado_en,
    )


@router.get("/usuarios", response_model=list[UsuarioAdminOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_required),
):
    """Lista todos los usuarios del sistema ordenados por id."""
    usuarios = db.query(Usuario).order_by(Usuario.id.asc()).all()
    return [_usuario_out(u) for u in usuarios]


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
        fijado=data.fijado,
        es_demo=data.es_demo,
    )
    db.add(nuevo_u)
    db.flush()

    registrar(
        db, admin, "CREAR_USUARIO", "usuario", nuevo_u.id,
        f"usuario={nuevo_u.usuario} rol={rol.nombre} fijado={nuevo_u.fijado} demo={nuevo_u.es_demo}",
    )
    from app.services.sync import encolar_sync

    encolar_sync(
        db,
        tipo="CREAR_USUARIO",
        entidad="usuario",
        payload={
            "id": nuevo_u.id,
            "nombre": nuevo_u.nombre,
            "usuario": nuevo_u.usuario,
            "rol_id": nuevo_u.rol_id,
            "password_hash": nuevo_u.password_hash,
            "activo": nuevo_u.activo,
            "fijado": nuevo_u.fijado,
            "es_demo": nuevo_u.es_demo,
        },
        entidad_id=nuevo_u.id,
        dispositivo_id=f"ADMIN_{admin.id}",
    )
    safe_commit(db)
    db.refresh(nuevo_u)
    return _usuario_out(nuevo_u)


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
    from app.services.sync import encolar_sync

    encolar_sync(
        db,
        tipo="MODIFICAR_PASSWORD",
        entidad="usuario",
        payload={
            "usuario_id": u.id,
            "nueva_password_hash": u.password_hash,
        },
        entidad_id=u.id,
        dispositivo_id=f"ADMIN_{admin.id}",
    )
    safe_commit(db)
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
    safe_commit(db)
    db.refresh(u)
    return _usuario_out(u)


@router.put("/usuarios/{usuario_id}/marcas", response_model=UsuarioAdminOut)
def cambiar_marcas_usuario(
    usuario_id: int,
    data: UsuarioMarcasUpdateIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Fija/desfija una cuenta (protegida contra resets) y/o la marca como cuenta demo."""
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if data.es_demo and u.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu propia cuenta administradora no puede marcarse como demo.",
        )

    cambios = []
    if data.fijado is not None:
        u.fijado = data.fijado
        cambios.append(f"fijado={data.fijado}")
    if data.es_demo is not None:
        u.es_demo = data.es_demo
        cambios.append(f"demo={data.es_demo}")

    registrar(db, admin, "MARCAR_USUARIO", "usuario", u.id, f"usuario={u.usuario} " + " ".join(cambios))
    safe_commit(db)
    db.refresh(u)
    return _usuario_out(u)


# ============================================================
# PUESTA EN BLANCO GRANULAR (CON CLAVE DEL ADMIN)
# ============================================================
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from decimal import Decimal
from app.models import (
    Categoria,
    Cierre,
    ComponenteCombo,
    Compra,
    DetalleCompra,
    DetallePedido,
    DetalleReceta,
    HistorialAccion,
    Ingrediente,
    Mesa,
    MovimientoCaja,
    MovimientoInventario,
    Pago,
    Pedido,
    Preparado,
    Producto,
    RegistroSync,
    TurnoLaboral,
    Vale,
)


@router.get("/sistema/reset/resumen")
def resumen_reset(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Conteos para que el asistente de reset muestre cuánto se borraría en cada opción."""
    def _n(modelo, *crit):
        return db.query(func.count(modelo.id)).filter(*crit).scalar() or 0

    return {
        "pedidos_demo": _n(Pedido, Pedido.es_demo.is_(True)),
        "pedidos_total": _n(Pedido),
        "movimientos_caja_demo": _n(MovimientoCaja, MovimientoCaja.es_demo.is_(True)),
        "turnos_caja_demo": _n(Cierre, Cierre.es_demo.is_(True)),
        "usuarios_demo": _n(Usuario, Usuario.es_demo.is_(True)),
        "usuarios_fijados": _n(Usuario, Usuario.fijado.is_(True)),
        "usuarios_borrables": _n(Usuario, Usuario.fijado.is_(False), Usuario.id != admin.id),
        "ingredientes": _n(Ingrediente),
        "productos": _n(Producto),
        "categorias": _n(Categoria),
        "compras": _n(Compra),
    }


def _borrar_transacciones(db: Session, solo_demo: bool, r: dict) -> None:
    """Elimina transacciones. solo_demo=True => únicamente lo marcado es_demo."""
    ped_ids = select(Pedido.id).where(Pedido.es_demo.is_(True)) if solo_demo else select(Pedido.id)

    # 1) Inventario: revertir el efecto sobre el stock y borrar movimientos
    if solo_demo:
        filtro_mov = or_(MovimientoInventario.es_demo.is_(True), MovimientoInventario.pedido_id.in_(ped_ids))
    else:
        filtro_mov = MovimientoInventario.pedido_id.in_(ped_ids)

    for ing_id, total in (
        db.query(MovimientoInventario.ingrediente_id, func.sum(MovimientoInventario.cantidad))
        .filter(filtro_mov)
        .group_by(MovimientoInventario.ingrediente_id)
        .all()
    ):
        if total:
            db.query(Ingrediente).filter(Ingrediente.id == ing_id).update(
                {Ingrediente.stock_actual: func.greatest(Ingrediente.stock_actual - total, 0)},
                synchronize_session=False,
            )
    r["movimientos_inventario"] = db.query(MovimientoInventario).filter(filtro_mov).delete(synchronize_session=False)

    # 2) Caja
    if solo_demo:
        vale_ids = select(Vale.id).where(or_(Vale.es_demo.is_(True), Vale.pedido_id.in_(ped_ids)))
        r["movimientos_caja"] = db.query(MovimientoCaja).filter(
            or_(
                MovimientoCaja.es_demo.is_(True),
                MovimientoCaja.pedido_id.in_(ped_ids),
                MovimientoCaja.vale_id.in_(vale_ids),
            )
        ).delete(synchronize_session=False)
        r["vales"] = db.query(Vale).filter(
            or_(Vale.es_demo.is_(True), Vale.pedido_id.in_(ped_ids))
        ).delete(synchronize_session=False)
        r["pagos"] = db.query(Pago).filter(
            or_(Pago.es_demo.is_(True), Pago.pedido_id.in_(ped_ids))
        ).delete(synchronize_session=False)
    else:
        r["movimientos_caja"] = db.query(MovimientoCaja).delete(synchronize_session=False)
        r["vales"] = db.query(Vale).delete(synchronize_session=False)
        r["pagos"] = db.query(Pago).delete(synchronize_session=False)

    # 3) Preparados (referencian detalle_pedido y pedido)
    if solo_demo:
        # Un preparado real asignado a un pedido demo vuelve a quedar disponible
        db.query(Preparado).filter(
            Preparado.pedido_nuevo_id.in_(ped_ids),
            Preparado.pedido_origen_id.notin_(ped_ids),
            Preparado.es_demo.is_(False),
        ).update(
            {Preparado.pedido_nuevo_id: None, Preparado.estado: "DISPONIBLE", Preparado.asignado_en: None},
            synchronize_session=False,
        )
        r["preparados"] = db.query(Preparado).filter(
            or_(
                Preparado.es_demo.is_(True),
                Preparado.pedido_origen_id.in_(ped_ids),
                Preparado.pedido_nuevo_id.in_(ped_ids),
            )
        ).delete(synchronize_session=False)
    else:
        r["preparados"] = db.query(Preparado).delete(synchronize_session=False)

    # 4) Pedidos y detalles
    r["detalles_pedido"] = db.query(DetallePedido).filter(DetallePedido.pedido_id.in_(ped_ids)).delete(
        synchronize_session=False
    )

    # 5) Turnos de caja (desvincular referencias de registros que se conservan)
    if solo_demo:
        cierres_demo = select(Cierre.id).where(Cierre.es_demo.is_(True))
        db.query(Pago).filter(Pago.cierre_id.in_(cierres_demo)).update({Pago.cierre_id: None}, synchronize_session=False)
        db.query(MovimientoCaja).filter(MovimientoCaja.cierre_id.in_(cierres_demo)).update(
            {MovimientoCaja.cierre_id: None}, synchronize_session=False
        )
        r["pedidos"] = db.query(Pedido).filter(Pedido.es_demo.is_(True)).delete(synchronize_session=False)
        r["turnos_caja"] = db.query(Cierre).filter(Cierre.es_demo.is_(True)).delete(synchronize_session=False)
        r["turnos_laborales"] = db.query(TurnoLaboral).filter(TurnoLaboral.es_demo.is_(True)).delete(
            synchronize_session=False
        )
        r["auditoria"] = db.query(HistorialAccion).filter(HistorialAccion.es_demo.is_(True)).delete(
            synchronize_session=False
        )
        # Compras hechas con cuentas demo (su efecto en stock ya se revirtió vía movimientos)
        compras_demo = select(Compra.id).where(Compra.es_demo.is_(True))
        db.query(DetalleCompra).filter(DetalleCompra.compra_id.in_(compras_demo)).delete(synchronize_session=False)
        r["compras"] = db.query(Compra).filter(Compra.es_demo.is_(True)).delete(synchronize_session=False)
    else:
        r["pedidos"] = db.query(Pedido).delete(synchronize_session=False)
        r["turnos_caja"] = db.query(Cierre).delete(synchronize_session=False)
        r["turnos_laborales"] = db.query(TurnoLaboral).delete(synchronize_session=False)
        r["auditoria"] = db.query(HistorialAccion).delete(synchronize_session=False)
        try:
            db.query(RegistroSync).delete(synchronize_session=False)
        except Exception:
            pass

    # 6) Liberar mesas que ya no tienen pedido abierto
    abiertas = select(Pedido.mesa_id).where(
        Pedido.mesa_id.is_not(None), Pedido.estado.notin_(("PAGADO", "CERRADO", "CANCELADO"))
    )
    db.query(Mesa).filter(Mesa.id.notin_(abiertas)).update({"estado": "DISPONIBLE"}, synchronize_session=False)


def _borrar_inventario(db: Session, r: dict) -> None:
    r["movimientos_inventario"] = r.get("movimientos_inventario", 0) + db.query(MovimientoInventario).delete(
        synchronize_session=False
    )
    db.query(DetalleCompra).delete(synchronize_session=False)
    r["compras"] = r.get("compras", 0) + db.query(Compra).delete(synchronize_session=False)
    db.query(Ingrediente).update({"stock_actual": Decimal("0")}, synchronize_session=False)
    r["stock_en_cero"] = True


def _borrar_insumos(db: Session, r: dict) -> None:
    r["recetas"] = db.query(DetalleReceta).delete(synchronize_session=False)
    r["insumos"] = db.query(Ingrediente).delete(synchronize_session=False)


def _borrar_menu(db: Session, r: dict) -> None:
    db.query(ComponenteCombo).delete(synchronize_session=False)
    r["recetas"] = r.get("recetas", 0) + db.query(DetalleReceta).delete(synchronize_session=False)
    db.query(Producto).update({Producto.empaque_llevar_id: None}, synchronize_session=False)
    r["productos"] = db.query(Producto).delete(synchronize_session=False)
    r["categorias"] = db.query(Categoria).delete(synchronize_session=False)


def _borrar_usuarios(db: Session, admin: Usuario, r: dict) -> None:
    """Elimina cuentas NO fijadas (jamás la del admin actual). Si una cuenta tiene historial que
    no se pudo borrar, se DESACTIVA en lugar de eliminarse (integridad referencial)."""
    candidatos = [
        (u.id, u.usuario)
        for u in db.query(Usuario).filter(Usuario.fijado.is_(False), Usuario.id != admin.id).all()
    ]
    eliminados, desactivados = [], []
    for uid, uname in candidatos:
        sp = db.begin_nested()
        try:
            db.query(TurnoLaboral).filter(TurnoLaboral.usuario_id == uid).delete(synchronize_session=False)
            db.query(HistorialAccion).filter(HistorialAccion.usuario_id == uid).delete(synchronize_session=False)
            db.query(Usuario).filter(Usuario.id == uid).delete(synchronize_session=False)
            db.flush()
            sp.commit()
            eliminados.append(uname)
        except IntegrityError:
            sp.rollback()
            db.query(Usuario).filter(Usuario.id == uid).update({"activo": False}, synchronize_session=False)
            desactivados.append(uname)
    r["usuarios_eliminados"] = eliminados
    r["usuarios_desactivados_por_historial"] = desactivados


@router.post("/sistema/reset")
def reset_sistema(
    data: ResetSistemaIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_required),
):
    """Asistente de puesta en blanco granular.

    - Exige la contraseña del administrador con la sesión activa.
    - Nunca elimina cuentas fijadas ni la cuenta del administrador que ejecuta el reset.
    - `solo_demo` borra única y exclusivamente lo generado por cuentas demo.
    """
    if not verify_password(data.password_admin, admin.password_hash):
        # 403 (no 401): el cliente HTTP cierra sesión ante un 401.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contraseña de administrador incorrecta")

    if not any((data.solo_demo, data.transacciones, data.inventario, data.insumos, data.menu, data.usuarios)):
        raise HTTPException(status_code=422, detail="Selecciona al menos una opción para restablecer")

    todo_tx = data.transacciones or data.menu          # menu exige borrar todas las transacciones
    inv = data.inventario or data.insumos              # insumos exige limpiar inventario
    solo_demo = data.solo_demo and not todo_tx

    resumen: dict = {}
    try:
        if todo_tx:
            _borrar_transacciones(db, solo_demo=False, r=resumen)
        elif solo_demo:
            _borrar_transacciones(db, solo_demo=True, r=resumen)
        if inv:
            _borrar_inventario(db, resumen)
        if data.insumos:
            _borrar_insumos(db, resumen)
        if data.menu:
            _borrar_menu(db, resumen)
        if data.usuarios:
            _borrar_usuarios(db, admin, resumen)

        alcance = [
            n for n, activo in (
                ("solo_demo", solo_demo), ("transacciones", todo_tx), ("inventario", inv),
                ("insumos", data.insumos), ("menu", data.menu), ("usuarios", data.usuarios),
            ) if activo
        ]
        registrar(
            db, admin, "RESET_SISTEMA", "sistema", None,
            f"alcance={','.join(alcance)} resumen={resumen}",
        )
        safe_commit(db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al restablecer el sistema: {exc}")

    return {
        "status": "ok",
        "mensaje": "Restablecimiento completado. Las cuentas fijadas y tu sesión se conservaron.",
        "detalle": resumen,
    }

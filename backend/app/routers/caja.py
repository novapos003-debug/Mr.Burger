from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import admin_required, cashier_required
from app.database import get_db
from app.models import Cierre, DetallePedido, MovimientoCaja, Pago, Pedido, Usuario, Vale
from app.schemas import (
    CierreCerrarIn,
    CierreOut,
    CobroIn,
    CobroOut,
    DevolucionIn,
    MovimientoCajaIn,
    MovimientoCajaOut,
    PagoOut,
    TurnoAperturaIn,
    ValeCobroIn,
    ValeOut,
)
from app.services.caja import (
    abrir_turno,
    cerrar_turno,
    cobrar_pedido,
    cobrar_vale,
    devolver_pago,
    registrar_movimiento,
    turno_abierto,
    obtener_turno_actual_con_metricas,
)
from app.services.websocket import ws_manager

router = APIRouter(prefix="/caja", tags=["caja"])


def _get_pedido(db: Session, pedido_id: int, lock: bool = False) -> Pedido:
    q = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.mesa),
            joinedload(Pedido.detalles).joinedload(DetallePedido.producto),
        )
        .filter(Pedido.id == pedido_id)
    )
    if lock:
        q = q.with_for_update(of=Pedido)
    pedido = q.first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


@router.post("/pedidos/{pedido_id}/cobrar", response_model=CobroOut)
async def cobrar(
    pedido_id: int,
    data: CobroIn,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Cobra un pedido (uno o varios métodos). Caja es el único rol que ve dinero."""
    pedido = _get_pedido(db, pedido_id, lock=True)
    if not turno_abierto(db):
        raise HTTPException(
            status_code=409,
            detail="No hay un turno de caja abierto. Debe abrir turno con la base inicial antes de cobrar.",
        )
    if pedido.estado == "CANCELADO":
        raise HTTPException(status_code=409, detail="El pedido está cancelado")
    if pedido.estado in ("CERRADO", "PAGADO") or pedido.pagado_en is not None:
        raise HTTPException(status_code=409, detail="El pedido ya fue cobrado o cerrado")

    try:
        resultado = cobrar_pedido(db, pedido, data, cajero)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    pedido = resultado["pedido"]
    await ws_manager.broadcast(
        {
            "evento": "pedido_pagado",
            # Sin montos: el evento llega a TODOS los dispositivos (mesero/cocina no ven dinero).
            "data": {
                "pedido_id": pedido.id,
                "consecutivo": pedido.consecutivo,
                "estado": pedido.estado,
                "pagado": pedido.pagado_en is not None,
            },
        }
    )
    return CobroOut(
        pedido_id=pedido.id,
        consecutivo=pedido.consecutivo,
        total=pedido.total,
        pagado=pedido.pagado_en is not None,
        pagos=[PagoOut.model_validate(p) for p in resultado["pagos"]],
        vales=[ValeOut.model_validate(v) for v in resultado["vales"]],
    )


@router.get("/pedidos/{pedido_id}/pagos", response_model=list[PagoOut])
def listar_pagos(
    pedido_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    _get_pedido(db, pedido_id)
    return (
        db.query(Pago)
        .filter(Pago.pedido_id == pedido_id)
        .order_by(Pago.id)
        .all()
    )


@router.post("/pagos/{pago_id}/devolver", response_model=PagoOut)
def devolver(
    pago_id: int,
    data: DevolucionIn,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Devuelve un pago con motivo obligatorio (queda en el historial de caja)."""
    pago = (
        db.query(Pago)
        .options(joinedload(Pago.pedido).joinedload(Pedido.mesa))
        .filter(Pago.id == pago_id)
        .first()
    )
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    try:
        pago = devolver_pago(db, pago, data.motivo, cajero)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return pago


@router.get("/vales", response_model=list[ValeOut])
def listar_vales(
    estado: str | None = None,
    pedido_id: int | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    q = db.query(Vale)
    if estado:
        q = q.filter(Vale.estado == estado)
    if pedido_id is not None:
        q = q.filter(Vale.pedido_id == pedido_id)
    return q.order_by(Vale.id.desc()).limit(200).all()


@router.post("/vales/{vale_id}/cobrar", response_model=ValeOut)
def cobrar_vale_endpoint(
    vale_id: int,
    data: ValeCobroIn | None = None,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """El cliente paga su pagaré: queda COBRADO e ingresa el dinero a caja."""
    vale = db.get(Vale, vale_id)
    if not vale:
        raise HTTPException(status_code=404, detail="Vale no encontrado")
    descripcion = data.descripcion if data else None
    try:
        cobrar_vale(db, vale, cajero, descripcion)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return vale


@router.get("/movimientos", response_model=list[MovimientoCajaOut])
def listar_movimientos(
    categoria: str | None = None,
    tipo: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    q = db.query(MovimientoCaja)
    if categoria:
        q = q.filter(MovimientoCaja.categoria == categoria)
    if tipo:
        q = q.filter(MovimientoCaja.tipo == tipo)
    return q.order_by(MovimientoCaja.id.desc()).limit(200).all()


# ============================================================
# TURNO DE CAJA (apertura + cierre)  /  ENTRADAS-EGRESOS ADMIN
# ============================================================

def _cierre_to_out(db: Session, c: Cierre) -> CierreOut:
    out = CierreOut.model_validate(c)
    if c.usuario:
        out.usuario_nombre = c.usuario.nombre
    else:
        u = db.get(Usuario, c.usuario_id)
        if u:
            out.usuario_nombre = u.nombre
    # Recuperar base inicial de apertura
    mov_base = (
        db.query(MovimientoCaja)
        .filter(MovimientoCaja.cierre_id == c.id, MovimientoCaja.categoria == "CAMBIO_INICIAL")
        .first()
    )
    if mov_base:
        out.monto_inicial = mov_base.valor
    return out


@router.get("/turno", response_model=CierreOut | None)
def ver_turno(
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    """Turno de caja abierto actualmente con métricas acumuladas en vivo (o null si no hay ninguno)."""
    c = obtener_turno_actual_con_metricas(db)
    if not c:
        return None
    return _cierre_to_out(db, c)


@router.post("/turno/abrir", response_model=CierreOut, status_code=201)
def abrir_turno_endpoint(
    data: TurnoAperturaIn,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Abre el turno de caja. Solo puede existir un turno abierto a la vez."""
    try:
        c = abrir_turno(db, cajero, data.monto_inicial)
        return _cierre_to_out(db, c)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/turno/cerrar", response_model=CierreOut)
async def cerrar_turno_endpoint(
    data: CierreCerrarIn | None = None,
    db: Session = Depends(get_db),
    cajero: Usuario = Depends(cashier_required),
):
    """Cierra el turno abierto y congela el fotograma del turno."""
    cierre = turno_abierto(db)
    if cierre is None:
        raise HTTPException(status_code=409, detail="No hay un turno de caja abierto")
    try:
        res = cerrar_turno(db, cierre, cajero, data.notas if data else None)
        return _cierre_to_out(db, res)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/movimientos", response_model=MovimientoCajaOut, status_code=201)
def crear_movimiento(
    data: MovimientoCajaIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(cashier_required),
):
    """Entrada/egreso manual de caja o gastos operativos (cajero o admin con turno abierto)."""
    return registrar_movimiento(db, usuario, data)


@router.get("/cierres", response_model=list[CierreOut])
def listar_cierres(
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    cierres = db.query(Cierre).options(joinedload(Cierre.usuario)).order_by(Cierre.id.desc()).limit(100).all()
    return [_cierre_to_out(db, c) for c in cierres]


@router.get("/cierres/{cierre_id}", response_model=CierreOut)
def obtener_cierre(
    cierre_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(cashier_required),
):
    cierre = db.query(Cierre).options(joinedload(Cierre.usuario)).filter(Cierre.id == cierre_id).first()
    if not cierre:
        raise HTTPException(status_code=404, detail="Cierre no encontrado")
    return _cierre_to_out(db, cierre)


@router.post("/abrir-cajon")
def abrir_cajon_monedero_fisico(
    _: Usuario = Depends(cashier_required),
):
    """Envía el pulso estándar ESC/POS RJ11 a la impresora térmica Windows conectada para patear la gaveta monedero."""
    import sys
    if sys.platform != "win32":
        return {"ok": False, "mensaje": "Comando de puerto directo compatible con servidor Windows"}

    import ctypes
    from ctypes import wintypes

    class DOC_INFO_1W(ctypes.Structure):
        _fields_ = [
            ("pDocName", wintypes.LPCWSTR),
            ("pOutputFile", wintypes.LPCWSTR),
            ("pDatatype", wintypes.LPCWSTR),
        ]

    class PRINTER_INFO_1W(ctypes.Structure):
        _fields_ = [
            ("flags", wintypes.DWORD),
            ("pDescription", wintypes.LPCWSTR),
            ("pName", wintypes.LPCWSTR),
            ("pComment", wintypes.LPCWSTR),
        ]

    winspool = ctypes.WinDLL("winspool.drv")

    # 1. Obtener lista de impresoras candidatas
    candidatas: list[str] = []

    # A) Impresora predeterminada
    buf_def = ctypes.create_unicode_buffer(512)
    pcb_def = wintypes.DWORD(512)
    if winspool.GetDefaultPrinterW(buf_def, ctypes.byref(pcb_def)) and buf_def.value:
        candidatas.append(buf_def.value)

    # B) Enumerar todas las impresoras del sistema
    try:
        flags = 2 | 4  # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
        pcb_needed = wintypes.DWORD(0)
        pc_returned = wintypes.DWORD(0)
        winspool.EnumPrintersW(flags, None, 1, None, 0, ctypes.byref(pcb_needed), ctypes.byref(pc_returned))
        if pcb_needed.value > 0:
            buf_enum = ctypes.create_string_buffer(pcb_needed.value)
            if winspool.EnumPrintersW(flags, None, 1, buf_enum, pcb_needed.value, ctypes.byref(pcb_needed), ctypes.byref(pc_returned)):
                printers_arr = ctypes.cast(buf_enum, ctypes.POINTER(PRINTER_INFO_1W))
                for i in range(pc_returned.value):
                    pname = printers_arr[i].pName
                    if pname and pname not in candidatas:
                        candidatas.append(pname)
    except Exception:
        pass

    # C) Fallback de nombres comunes en caso de fallo de enumeración
    fallbacks = ["STAR-TP80NC-M", "SAT 22TUS (copy 1)", "SAT 22TUS", "POS-80", "POS-58", "XP-80", "XP-58", "CAJAP"]
    for f in fallbacks:
        if f not in candidatas:
            candidatas.append(f)

    # Secuencia combinada universal para abrir gaveta en Pin 2, Pin 5 y DLE DC4
    PULSO_CAJON_UNIVERSAL = bytes([
        0x1B, 0x70, 0x00, 0x19, 0xFA,  # ESC p 0 25 250 (Pin 2, estándar Epson/China)
        0x1B, 0x70, 0x01, 0x19, 0xFA,  # ESC p 1 25 250 (Pin 5, estándar alternativo)
        0x10, 0x14, 0x01, 0x00, 0x05,  # DLE DC4 n r t (Real-time kick)
        0x07,                          # BEL (Star Micronics / genéricas)
    ])

    hPrinter = wintypes.HANDLE()
    enviado = False
    impresora_usada = ""

    for nombre_imp in candidatas:
        # Ignorar impresoras virtuales de PDF/OneNote/Fax para no generar archivos basura
        nombre_lower = nombre_imp.lower()
        if any(v in nombre_lower for v in ("pdf", "onenote", "fax", "xps", "document writer")):
            continue

        if winspool.OpenPrinterW(nombre_imp, ctypes.byref(hPrinter), None):
            try:
                doc_info = DOC_INFO_1W("Abrir Cajon POS", None, "RAW")
                job_id = winspool.StartDocPrinterW(hPrinter, 1, ctypes.byref(doc_info))
                if job_id > 0:
                    winspool.StartPagePrinter(hPrinter)
                    written = wintypes.DWORD()
                    winspool.WritePrinter(hPrinter, PULSO_CAJON_UNIVERSAL, len(PULSO_CAJON_UNIVERSAL), ctypes.byref(written))
                    winspool.EndPagePrinter(hPrinter)
                    winspool.EndDocPrinter(hPrinter)
                    enviado = True
                    impresora_usada = nombre_imp
            except Exception:
                pass
            finally:
                winspool.ClosePrinter(hPrinter)
            if enviado:
                break

    if enviado:
        return {"ok": True, "impresora": impresora_usada, "mensaje": f"Pulso enviado exitosamente a la impresora '{impresora_usada}'"}
    return {"ok": False, "mensaje": "No se detectó ninguna impresora térmica física en Windows"}


"""Impresora térmica de la caja: envío directo de bytes ESC/POS por la cola de Windows.

El navegador no puede tomar la impresora por USB cuando Windows ya le instaló su controlador
("acceso denegado"). La caja sí puede: le entrega los bytes a la cola de impresión en modo RAW
y el controlador los pasa tal cual a la impresora. Así se imprime la tirilla y se abre el cajón.
"""
import sys

ESC_INICIAR = b"\x1b\x40"
# FS . saca a las impresoras genéricas del modo de caracteres chinos; ESC t 2 elige la página
# de códigos 850, que trae las tildes y la ñ.
ESC_ESPANOL = b"\x1c\x2e\x1b\x74\x02"
ESC_CORTAR = b"\n\n\n\n\x1d\x56\x41\x03"
# ESC p en el pin 2 y en el pin 5: según la marca, el cajón está cableado a uno u otro.
ESC_ABRIR_CAJON = b"\x1b\x70\x00\x19\xfa\x1b\x70\x01\x19\xfa"

_VIRTUALES = ("pdf", "onenote", "fax", "xps", "document writer")
_NOMBRES_COMUNES = ("STAR-TP80NC-M", "POS-80", "POS-58", "XP-80", "XP-58")


def bytes_de_tirilla(texto: str, abrir_cajon: bool = False) -> bytes:
    cuerpo = texto.replace("\r\n", "\n").encode("cp850", errors="replace")
    return ESC_INICIAR + (ESC_ABRIR_CAJON if abrir_cajon else b"") + ESC_ESPANOL + cuerpo + ESC_CORTAR


def bytes_de_cajon() -> bytes:
    return ESC_INICIAR + ESC_ABRIR_CAJON


def enviar_a_impresora(datos: bytes, documento: str) -> str | None:
    """Envía los bytes a la impresora térmica de este equipo. Devuelve su nombre, o None si
    no hay ninguna (o si el servidor no es Windows, como el espejo de la nube)."""
    if sys.platform != "win32":
        return None

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
    winspool.OpenPrinterW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p]
    winspool.StartDocPrinterW.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(DOC_INFO_1W)]
    winspool.StartDocPrinterW.restype = wintypes.DWORD
    winspool.StartPagePrinter.argtypes = [wintypes.HANDLE]
    winspool.WritePrinter.argtypes = [wintypes.HANDLE, ctypes.c_char_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    winspool.EndPagePrinter.argtypes = [wintypes.HANDLE]
    winspool.EndDocPrinter.argtypes = [wintypes.HANDLE]
    winspool.ClosePrinter.argtypes = [wintypes.HANDLE]

    # La predeterminada de Windows va primero: es la que el restaurante eligió para la caja.
    candidatas: list[str] = []
    buf_def = ctypes.create_unicode_buffer(512)
    pcb_def = wintypes.DWORD(512)
    if winspool.GetDefaultPrinterW(buf_def, ctypes.byref(pcb_def)) and buf_def.value:
        candidatas.append(buf_def.value)

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

    for nombre in _NOMBRES_COMUNES:
        if nombre not in candidatas:
            candidatas.append(nombre)

    for nombre in candidatas:
        # Las impresoras virtuales (PDF, XPS, fax) solo generarían archivos basura.
        if any(v in nombre.lower() for v in _VIRTUALES):
            continue
        handle = wintypes.HANDLE()
        if not winspool.OpenPrinterW(nombre, ctypes.byref(handle), None):
            continue
        try:
            doc = DOC_INFO_1W(documento, None, "RAW")
            if not winspool.StartDocPrinterW(handle, 1, ctypes.byref(doc)):
                continue
            winspool.StartPagePrinter(handle)
            escritos = wintypes.DWORD()
            ok = winspool.WritePrinter(handle, datos, len(datos), ctypes.byref(escritos))
            winspool.EndPagePrinter(handle)
            winspool.EndDocPrinter(handle)
            if ok and escritos.value == len(datos):
                return nombre
        finally:
            winspool.ClosePrinter(handle)
    return None

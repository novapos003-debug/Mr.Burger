from app.models.auditoria import HistorialAccion
from app.models.caja import Cierre, MovimientoCaja, Pago, Vale
from app.models.catalogo import (
    Categoria,
    CategoriaInsumo,
    ComponenteCombo,
    DetalleReceta,
    Ingrediente,
    Producto,
    Proveedor,
    TipoCategoria,
)
from app.models.compra import Compra, DetalleCompra
from app.models.configuracion import Configuracion
from app.models.inventario import MovimientoInventario
from app.models.pedidos import DetallePedido, Mesa, Pedido
from app.models.preparado import Preparado
from app.models.sync import RegistroSync
from app.models.usuario import Rol, Usuario
from app.models.asistencia import TurnoLaboral

import app.core.demo  # noqa: E402,F401  (registra los listeners de trazabilidad demo)
import app.core.replicacion  # noqa: E402,F401  (registra la captura de cambios para la sincronización)

__all__ = [
    "Categoria",
    "CategoriaInsumo",
    "Cierre",
    "ComponenteCombo",
    "Compra",
    "Configuracion",
    "DetalleCompra",
    "DetallePedido",
    "DetalleReceta",
    "HistorialAccion",
    "Ingrediente",
    "Mesa",
    "MovimientoCaja",
    "MovimientoInventario",
    "Pago",
    "Pedido",
    "Preparado",
    "Producto",
    "Proveedor",
    "RegistroSync",
    "Rol",
    "TipoCategoria",
    "TurnoLaboral",
    "Usuario",
    "Vale",
]
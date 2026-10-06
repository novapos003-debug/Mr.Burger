"""Trazabilidad de cuentas demo.

Todo registro transaccional creado por un usuario con `usuario.es_demo = TRUE`
(o ligado a un pedido demo) queda estampado con `es_demo = TRUE` en el momento
del INSERT. Esto permite borrar de forma exclusiva y segura lo generado en
pruebas/capacitación sin tocar la operación real.
"""
from sqlalchemy import event, text

from app.models.asistencia import TurnoLaboral
from app.models.auditoria import HistorialAccion
from app.models.caja import Cierre, MovimientoCaja, Pago, Vale
from app.models.compra import Compra
from app.models.inventario import MovimientoInventario
from app.models.pedidos import Pedido
from app.models.preparado import Preparado

# Campos que pueden delatar el origen demo de un registro
_CAMPOS_USUARIO = ("usuario_id", "cobrado_por")
_CAMPOS_PEDIDO = ("pedido_id", "pedido_origen_id")


def _usuario_es_demo(connection, usuario_id) -> bool:
    if not usuario_id:
        return False
    row = connection.execute(
        text("SELECT es_demo FROM usuario WHERE id = :i"), {"i": usuario_id}
    ).first()
    return bool(row[0]) if row else False


def _pedido_es_demo(connection, pedido_id) -> bool:
    if not pedido_id:
        return False
    row = connection.execute(
        text("SELECT es_demo FROM pedido WHERE id = :i"), {"i": pedido_id}
    ).first()
    return bool(row[0]) if row else False


def _estampar(mapper, connection, target) -> None:
    if getattr(target, "es_demo", False):
        return
    for campo in _CAMPOS_USUARIO:
        if _usuario_es_demo(connection, getattr(target, campo, None)):
            target.es_demo = True
            return
    for campo in _CAMPOS_PEDIDO:
        if _pedido_es_demo(connection, getattr(target, campo, None)):
            target.es_demo = True
            return
    target.es_demo = False


MODELOS_TRAZABLES = (
    Pedido,
    Pago,
    Vale,
    MovimientoCaja,
    Cierre,
    TurnoLaboral,
    MovimientoInventario,
    Compra,
    HistorialAccion,
    Preparado,
)

for _modelo in MODELOS_TRAZABLES:
    event.listen(_modelo, "before_insert", _estampar)

from sqlalchemy.orm import Session

from app.models import HistorialAccion


def registrar(
    db: Session,
    usuario,
    accion: str,
    entidad: str | None = None,
    entidad_id: int | None = None,
    detalle: str | None = None,
) -> HistorialAccion:
    """Agrega una entrada al historial SIN commitear.

    El llamador debe incluirla en su transacción para que quede exactamente junto
    a la operación que describe (si la operación falla, el registro también).
    """
    registro = HistorialAccion(
        usuario_id=getattr(usuario, "id", None),
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
    )
    db.add(registro)
    return registro

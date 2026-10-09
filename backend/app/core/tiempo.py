from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.config import settings

_BOGOTA_FALLBACK = timezone(timedelta(hours=-5))


def zona():
    try:
        return ZoneInfo(settings.ZONA_HORARIA)
    except Exception:
        try:
            return ZoneInfo("America/Bogota")
        except Exception:
            return _BOGOTA_FALLBACK


def ahora_local() -> datetime:
    """Hora actual en la zona del restaurante (no en UTC del contenedor).

    El consecutivo diario, 'hoy' y la apertura/cierre de turno deben regirse por la
    hora local de Cali, no por UTC: en Colombia (UTC-5) el día UTC cambia a las 7pm.
    """
    return datetime.now(zona())


def fecha_local() -> date:
    return ahora_local().date()

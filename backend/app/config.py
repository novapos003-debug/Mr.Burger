import secrets
from pathlib import Path

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_BASE_DIR = _BACKEND_DIR.parent
_ENV_PATH = _BASE_DIR / ".env"
_ARCHIVO_CLAVE = _BACKEND_DIR / ".secret_key"


class Settings(BaseSettings):
    ENTORNO: str = "desarrollo"
    # Clave con la que se firman las sesiones. NO tiene valor por defecto en el código:
    # en la nube se define como variable de entorno; en la caja se genera sola (ver abajo).
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    ZONA_HORARIA: str = "America/Bogota"  # el consecutivo diario y "hoy" usan hora local del local
    DATABASE_URL: str = ""  # vacío = base local por defecto (ver database.py)

    # Sincronización y Espejo en la Nube
    MODO_CEREBRO: str = "LOCAL"  # LOCAL = Servidor en Caja; NUBE = Servidor Espejo en Cloud
    SUCURSAL_ID: str = "SUC-01"  # Identificador único de sucursal
    CLOUD_SYNC_ENABLED: bool = True
    CLOUD_SYNC_URL: str = "https://mrburger-api.onrender.com"  # URL del servidor en la nube (Render)
    # Secreto compartido entre la caja y la nube. Sin valor por defecto: si está vacío, la
    # sincronización queda deshabilitada en vez de funcionar con una clave conocida.
    CLOUD_SYNC_TOKEN: str = ""
    SYNC_INTERVAL_SECONDS: int = 5  # Intervalo máximo entre ciclos; los cambios nuevos se envían al instante

    class Config:
        env_file = (str(_ENV_PATH), ".env")
        extra = "ignore"


def _clave_de_esta_instalacion() -> str:
    """Clave de sesiones propia de esta máquina. Se crea la primera vez y se guarda en
    `backend/.secret_key` (archivo ignorado por git). Así cada instalación tiene la suya
    sin que nadie tenga que escribirla ni quede publicada en el repositorio."""
    try:
        if _ARCHIVO_CLAVE.exists():
            clave = _ARCHIVO_CLAVE.read_text(encoding="utf-8").strip()
            if len(clave) >= 32:
                return clave
        clave = secrets.token_urlsafe(48)
        _ARCHIVO_CLAVE.write_text(clave, encoding="utf-8")
        return clave
    except OSError:
        # Sin permiso de escritura: clave válida solo hasta el próximo reinicio
        return secrets.token_urlsafe(48)


settings = Settings()

if not settings.SECRET_KEY:
    if settings.MODO_CEREBRO == "NUBE":
        raise RuntimeError("Falta la variable de entorno SECRET_KEY en el servidor de la nube")
    settings.SECRET_KEY = _clave_de_esta_instalacion()

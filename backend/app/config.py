from pathlib import Path
from pydantic_settings import BaseSettings

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _BASE_DIR / ".env"


class Settings(BaseSettings):
    ENTORNO: str = "desarrollo"
    SECRET_KEY: str = "ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    ZONA_HORARIA: str = "America/Bogota"  # el consecutivo diario y "hoy" usan hora local del local

    # Sincronización y Espejo en la Nube
    MODO_CEREBRO: str = "LOCAL"  # LOCAL = Servidor en Caja; NUBE = Servidor Espejo en Cloud
    SUCURSAL_ID: str = "SUC-01"  # Identificador único de sucursal
    CLOUD_SYNC_ENABLED: bool = True
    CLOUD_SYNC_URL: str = "https://mrburger-api.onrender.com"  # URL del servidor en la nube (Render)
    CLOUD_SYNC_TOKEN: str = "mrburger_sync_secret_token_2026"  # Token criptográfico de sincronización
    SYNC_INTERVAL_SECONDS: int = 10  # Intervalo de sondeo/envío en segundos
    # Credenciales del admin de la nube que usa el worker para PULL/replicación (opcionales).
    # Si se definen se prueban primero; permiten cambiar las claves por defecto sin romper la sincronización.
    CLOUD_SYNC_USER: str = ""
    CLOUD_SYNC_PASSWORD: str = ""

    class Config:
        env_file = (str(_ENV_PATH), ".env")
        extra = "ignore"


settings = Settings()
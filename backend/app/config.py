from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENTORNO: str = "desarrollo"
    SECRET_KEY: str = "dev_secret_cambiar_en_produccion"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    ZONA_HORARIA: str = "America/Bogota"  # el consecutivo diario y "hoy" usan hora local del local

    # Sincronización y Espejo en la Nube
    MODO_CEREBRO: str = "LOCAL"  # LOCAL = Servidor en Caja; NUBE = Servidor Espejo en Cloud
    SUCURSAL_ID: str = "SUC-01"  # Identificador único de sucursal
    CLOUD_SYNC_ENABLED: bool = True
    CLOUD_SYNC_URL: str = ""  # URL del servidor en la nube (ej. https://nube.mi-restaurante.com)
    CLOUD_SYNC_TOKEN: str = "dev_sync_token_punto_fijo_2026"  # Token criptográfico de sincronización
    SYNC_INTERVAL_SECONDS: int = 10  # Intervalo de sondeo/envío en segundos

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
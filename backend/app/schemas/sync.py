from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SyncOpIn(BaseModel):
    op_id: str = Field(min_length=8, max_length=64, description="UUID idempotente generado por el terminal")
    sucursal_id: str = Field(default="SUC-01", max_length=20)
    dispositivo_id: str = Field(min_length=2, max_length=50)
    tipo: str = Field(max_length=50, description="FILA (insertar o actualizar la fila) | BORRAR")
    entidad: str = Field(max_length=50, description="Nombre de la tabla")
    entidad_id: int | None = None
    entidad_uuid: str | None = None
    payload: dict
    origen: str = Field(default="LOCAL", pattern="^(LOCAL|NUBE)$")


class SyncOpOut(BaseModel):
    id: int
    op_id: str
    sucursal_id: str = "SUC-01"
    dispositivo_id: str
    tipo: str
    entidad: str
    entidad_id: int | None = None
    entidad_uuid: str | None = None
    payload: dict
    origen: str
    estado: str
    reintentos: int = 0
    ultimo_error: str | None = None
    resolucion_nota: str | None = None
    creado_en: datetime
    sincronizado_en: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SyncPushIn(BaseModel):
    dispositivo_id: str = Field(min_length=2, max_length=50, description="Identificador de la instalación (caja) que envía")
    operaciones: list[SyncOpIn] = Field(min_length=1, max_length=500)


class SyncOpResultado(BaseModel):
    """Resultado individual de cada operación del lote (la nube aísla los fallos por operación)."""

    op_id: str
    estado: str  # APLICADO | DUPLICADO | CONFLICTO | ERROR
    error: str | None = None


class SyncPushOut(BaseModel):
    procesadas: int
    duplicadas: int
    conflictos: int
    errores: int = 0
    operaciones: list[SyncOpOut]
    resultados: list[SyncOpResultado] = []


class SyncCambiosOut(BaseModel):
    """Cambios del panel web pendientes de aplicar en la caja."""

    espejo_id: str
    # Instalación (caja) vinculada a este espejo; "" si todavía ninguna. Con eso la caja sabe
    # si el espejo espera su copia completa aunque el identificador del espejo no haya cambiado.
    vinculada: str | None = None
    operaciones: list[SyncOpOut]


class SyncConfirmarIn(BaseModel):
    hasta_id: int = Field(ge=0)


class SyncReiniciarIn(BaseModel):
    confirmar: str


class SyncEstadoOut(BaseModel):
    cerebro_modo: str  # LOCAL | NUBE
    total_operaciones: int
    pendientes: int
    aplicadas: int
    conflictos: int
    ultima_sincronizacion: datetime | None = None
    online: bool = True
    sincronizando: bool = False
    ultimo_error: str | None = None
    sucursal_id: str = "SUC-01"

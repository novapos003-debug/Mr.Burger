from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time
from collections import defaultdict

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_db, safe_commit
from app.models import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory rate limiting simple: { ip: [timestamps] }
FAILED_LOGINS = defaultdict(list)
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutos

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UsuarioOut(BaseModel):
    id: int
    usuario: str
    nombre: str
    rol: str

    class Config:
        from_attributes = True

@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Extraer IP real detrás de reverse proxies (Render / Cloudflare / Nginx)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    key = f"{form_data.username.strip().lower()}_{ip}"
    now = time.time()

    # Purgar periódicamente si el diccionario crece demasiado
    if len(FAILED_LOGINS) > 2000:
        keys_to_del = [k for k, timestamps in FAILED_LOGINS.items() if not timestamps or now - timestamps[-1] > LOCKOUT_SECONDS]
        for k in keys_to_del:
            del FAILED_LOGINS[k]

    # Limpiar intentos viejos
    FAILED_LOGINS[key] = [t for t in FAILED_LOGINS[key] if now - t < LOCKOUT_SECONDS]
    if len(FAILED_LOGINS[key]) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos para este usuario. Intente nuevamente en 5 minutos."
        )

    user = db.query(Usuario).filter(Usuario.usuario == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        FAILED_LOGINS[key].append(now)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    # Reset en exito para liberar memoria
    if key in FAILED_LOGINS:
        del FAILED_LOGINS[key]
    
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UsuarioOut)
def me(current_user: Usuario = Depends(get_current_user)):
    return UsuarioOut(
        id=current_user.id,
        usuario=current_user.usuario,
        nombre=current_user.nombre,
        rol=current_user.rol.nombre,
    )


from app.schemas.admin import CambiarMiPasswordIn
from app.core.security import hash_password


@router.put("/cambiar-password")
def cambiar_mi_password(
    data: CambiarMiPasswordIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Permite a cualquier usuario cambiar su propia contraseña verificando la clave actual."""
    if not verify_password(data.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual no es correcta",
        )
    current_user.password_hash = hash_password(data.nueva_password)
    safe_commit(db)
    return {"status": "ok", "mensaje": "Contraseña cambiada exitosamente"}
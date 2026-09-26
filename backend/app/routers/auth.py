from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])


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
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(Usuario).filter(Usuario.usuario == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

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
    db.commit()
    return {"status": "ok", "mensaje": "Contraseña cambiada exitosamente"}
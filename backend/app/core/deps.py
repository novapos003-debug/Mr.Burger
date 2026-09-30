from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise credentials_exception

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise credentials_exception

    user = db.get(Usuario, user_id)
    if not user or not user.activo:
        raise credentials_exception
    return user


def require_roles(*roles: str):
    def checker(
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Usuario:
        if current_user.rol.nombre not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{current_user.rol.nombre}' sin permiso. Requiere: {', '.join(roles)}",
            )

        # Regla de Asistencia: Los roles operativos requieren un turno laboral abierto
        if current_user.rol.nombre != "admin":
            from app.models.asistencia import TurnoLaboral
            turno_activo = (
                db.query(TurnoLaboral)
                .filter(
                    TurnoLaboral.usuario_id == current_user.id,
                    TurnoLaboral.salida_en.is_(None),
                )
                .first()
            )
            if not turno_activo:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tu turno laboral ha sido cerrado o ha finalizado. Tu sesión no está activa.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return current_user

    return checker


admin_required = require_roles("admin")
cashier_required = require_roles("admin", "cajero")
kitchen_required = require_roles("admin", "cocina")
staff_required = require_roles("admin", "cajero", "mesero", "cocina")
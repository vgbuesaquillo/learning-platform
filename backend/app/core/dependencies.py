from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.core.security import decode_token
from app.domain.models import User
from uuid import UUID
import asyncio # Required for lifespan

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def require_instructor(current_user: User = Depends(get_current_user)) -> User:
    """Requires the user to be an instructor."""
    if not current_user.is_instructor:
        raise HTTPException(status_code=403, detail="Se requiere rol de instructor")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Requires the user to have admin privileges (currently, is_instructor is used as proxy)."""
    # For MVP, is_instructor is used as a proxy for admin privileges.
    # In the future, a dedicated 'is_admin' field might be added to the User model.
    if not current_user.is_instructor:
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador")
    return current_user


def require_own_resource(
    resource_user_id: UUID,
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifies that the user can only access their own resources unless they are an instructor."""
    if str(resource_user_id) != str(current_user.id) and not current_user.is_instructor:
        raise HTTPException(status_code=403, detail="Acceso denegado: recurso de otro usuario")
    return current_user
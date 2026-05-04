from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.core.security import decode_token
from app.domain.models import User

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
    if not current_user.is_instructor:
        raise HTTPException(status_code=403, detail="Se requiere rol de instructor")
    return current_user

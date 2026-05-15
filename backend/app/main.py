from __future__ import annotations
from fastapi import Depends, HTTPException, status, APIRouter, Body, FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.core.security import decode_token
from app.domain.models import User, UserProgress, LearningItem # Import UserProgress and LearningItem
from app.api.learning_items import router as learning_items_router

from app.core.config import settings
from uuid import UUID
import asyncio # Required for lifespan
from contextlib import asynccontextmanager

# No-op schedulers to satisfy lifespan hooks if not defined elsewhere

def start_scheduler():
    pass

def shutdown_scheduler():
    pass

security = HTTPBearer()

# API router for v1
api_router = APIRouter(prefix="/api/v1")


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

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    start_scheduler()
    yield
    # Shutdown logic
    shutdown_scheduler()

# FastAPI app instance
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan # Use the lifespan manager
)

# Register routers
from app.api.v1.auth import router as auth_router
api_router.include_router(auth_router)
from app.api.learning_items import router as learning_items_router
api_router.include_router(learning_items_router)
from app.api.progress import router as progress_router
api_router.include_router(progress_router)

# Health endpoint for container checks
@app.get("/health")
async def health():
    return {"status": "ok"}

# Include the main API router
app.include_router(api_router)

# Root endpoint
@api_router.get("/")
async def read_root():
    return {"message": "Welcome to the LearnPath API"}

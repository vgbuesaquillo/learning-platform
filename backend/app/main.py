from fastapi import Depends, HTTPException, status, APIRouter, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.core.security import decode_token
from app.domain.models import User, UserProgress, LearningItem # Import UserProgress and LearningItem
from app.domain.schemas import UserCreateSchema, UserSchema # Assuming these schemas exist
from app.core.config import settings
from uuid import UUID
import asyncio # Required for lifespan

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

# Example of how to use require_own_resource in a route:
# @api_router.get("/progress/dashboard/{user_id_param}")
# async def get_user_progress_dashboard(
#     user_id_param: UUID,
#     current_user: User = Depends(require_own_resource(resource_user_id=user_id_param)) # Pass the user_id_param here
# ):
#     # ... your logic ...
#     pass

# Register auth routes
from app.api.v1.auth import router as auth_router
api_router.include_router(auth_router)

# Register other routers (placeholder)
# from app.api.v1.themes import router as themes_router
# api_router.include_router(themes_router)

# from app.api.v1.evidence import router as evidence_router
# api_router.include_router(evidence_router)

# from app.api.v1.progress import router as progress_router
# api_router.include_router(progress_router)

# Mock routers to allow `main.py` to run without errors if they don't exist yet
# If these exist, they will be imported and used instead
try:
    from app.api.v1.themes import router as themes_router
    api_router.include_router(themes_router)
except ImportError:
    print("themes router not found, skipping import.")

try:
    from app.api.v1.evidence import router as evidence_router
    api_router.include_router(evidence_router)
except ImportError:
    print("evidence router not found, skipping import.")

try:
    from app.api.v1.progress import router as progress_router
    api_router.include_router(progress_router)
except ImportError:
    print("progress router not found, skipping import.")

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

# Include the main API router
app.include_router(api_router)

# Root endpoint
@api_router.get("/")
async def read_root():
    return {"message": "Welcome to the LearnPath API"}

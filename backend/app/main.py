import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.evidence import router as evidence_router, progress_router
from app.infrastructure.database import engine
from app.domain.models import Base

# Logging estructurado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas si no existen (en producción usar Alembic)
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas/verificadas", environment=settings.ENVIRONMENT)
    yield
    logger.info("Aplicación cerrada")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API de LearnPath — Plataforma de aprendizaje con medición de progreso real",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENVIRONMENT}

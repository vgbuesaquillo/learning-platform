from __future__ import annotations
from fastapi import Depends, HTTPException, status, APIRouter, Body, FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.core.security import decode_token
from app.domain.models import User, UserProgress, LearningItem # Import UserProgress and LearningItem
from app.core.config import settings
from contextlib import asynccontextmanager

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")

# Register routers
from app.api.auth import router as auth_router
api_router.include_router(auth_router)
from app.api.learning_items import router as learning_items_router
api_router.include_router(learning_items_router)
from app.api.progress import router as progress_router
api_router.include_router(progress_router)
from app.api.evidence import router as evidence_router
api_router.include_router(evidence_router)
from app.api.themes import router as themes_router
api_router.include_router(themes_router)
from app.api.activities import router as activities_router
api_router.include_router(activities_router)

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

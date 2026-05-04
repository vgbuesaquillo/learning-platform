from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.schemas import Theme as ThemeSchema, ThemeCreate, ThemeUpdate
from app.domain.models import Theme as ThemeModel # Import model for DB operations
from app.infrastructure.database import get_db
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

router = APIRouter(prefix="/themes", tags=["Themes"])

# --- Helper function to get theme by ID ---
def get_theme(db: Session, theme_id: UUID) -> ThemeModel:
    db_theme = db.query(ThemeModel).filter(ThemeModel.id == theme_id).first()
    if not db_theme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
    return db_theme

# --- CRUD Endpoints for Themes ---

@router.post("/", response_model=ThemeSchema, status_code=status.HTTP_201_CREATED)
def create_theme(
    theme: ThemeCreate, db: Session = Depends(get_db)
):
    # Check if theme name already exists
    if db.query(ThemeModel).filter(ThemeModel.name == theme.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Theme name already exists")

    db_theme = ThemeModel(
        id=UUID(), # Generate new UUID
        name=theme.name,
        description=theme.description,
        order=theme.order,
        is_active=theme.is_active
    )
    db.add(db_theme)
    db.commit()
    db.refresh(db_theme)
    return db_theme

@router.get("/", response_model=List[ThemeSchema])
def read_themes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    themes = db.query(ThemeModel).offset(skip).limit(limit).all()
    return themes

@router.get("/{theme_id}", response_model=ThemeSchema)
def read_theme(theme_id: UUID, db: Session = Depends(get_db)):
    db_theme = get_theme(db=db, theme_id=theme_id)
    return db_theme

@router.put("/{theme_id}", response_model=ThemeSchema)
def update_theme(
    theme_id: UUID,
    theme_update: ThemeUpdate,
    db: Session = Depends(get_db),
):
    db_theme = get_theme(db=db, theme_id=theme_id)

    # Check for name conflicts if the name is being updated
    if theme_update.name and theme_update.name != db_theme.name:
        if db.query(ThemeModel).filter(ThemeModel.name == theme_update.name).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Theme name already exists")

    # Update fields
    for field, value in theme_update.model_dump().items():
        if value is not None:
            setattr(db_theme, field, value)

    db.commit()
    db.refresh(db_theme)
    return db_theme

@router.delete("/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_theme(theme_id: UUID, db: Session = Depends(get_db)):
    db_theme = get_theme(db=db, theme_id=theme_id)
    db.delete(db_theme)
    db.commit()
    # No return value needed for 204

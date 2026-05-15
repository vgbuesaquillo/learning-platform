from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.schemas import (
    LearningItem as LearningItemSchema,
    LearningItemCreate,
    LearningItemUpdate,
)
from app.domain.models import LearningItem as LearningItemModel
from app.infrastructure.database import get_db
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

router = APIRouter(prefix="/learning-items", tags=["Learning Items"])

# --- Helper function to get a learning item by ID ---
def get_learning_item(db: Session, item_id: UUID) -> LearningItemModel:
    db_item = db.query(LearningItemModel).filter(LearningItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning item not found")
    return db_item

# --- CRUD Endpoints for Learning Items ---

@router.post("/", response_model=LearningItemSchema, status_code=status.HTTP_201_CREATED)
def create_learning_item(
    item: LearningItemCreate, db: Session = Depends(get_db)
):
    db_item = LearningItemModel(
        id=UUID(),
        theme_id=item.theme_id,
        item_type=item.item_type,
        content=item.content,
        item_metadata=item.item_metadata,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[LearningItemSchema])
def read_learning_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(LearningItemModel).offset(skip).limit(limit).all()
    return items

@router.get("/{item_id}", response_model=LearningItemSchema)
def read_learning_item(item_id: UUID, db: Session = Depends(get_db)):
    db_item = get_learning_item(db=db, item_id=item_id)
    return db_item

@router.put("/{item_id}", response_model=LearningItemSchema)
def update_learning_item(
    item_id: UUID,
    item_update: LearningItemUpdate,
    db: Session = Depends(get_db),
):
    db_item = get_learning_item(db=db, item_id=item_id)

    for field, value in item_update.model_dump().items():
        if value is not None:
            # Use item_metadata for updates for consistency with the model change
            setattr(db_item, 'item_metadata', value)

    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_learning_item(item_id: UUID, db: Session = Depends(get_db)):
    db_item = get_learning_item(db=db, item_id=item_id)
    db.delete(db_item)
    db.commit()


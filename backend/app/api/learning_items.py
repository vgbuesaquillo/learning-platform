from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.domain.schemas import (
    LearningItem as LearningItemSchema,
    LearningItemCreate,
    LearningItemUpdate,
    RecordInteractionResponse,
)
from app.domain.models import LearningItem as LearningItemModel
from app.domain.models import User, UserProgress, UserInteraction
from app.domain.services.knowledge_inference import KnowledgeInferenceService
from app.infrastructure.database import get_db
from app.core.dependencies import get_current_user
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
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


@router.post("/{item_id}/view", response_model=RecordInteractionResponse)
def view_learning_item(
    item_id: UUID,
    body: Optional[Dict[str, Any]] = Body(default={}),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records a user viewing/studying a learning item and updates mastery."""
    item = get_learning_item(db=db, item_id=item_id)

    inference_service = KnowledgeInferenceService(db)

    # Get or create UserProgress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.learning_item_id == item_id,
    ).first()

    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            theme_id=item.theme_id,
            learning_item_id=item_id,
            mastery_level=0.0,
            recurrence_score=0,
        )
        db.add(progress)
        db.flush()

    # Create UserInteraction record
    interaction = UserInteraction(
        user_id=current_user.id,
        learning_item_id=item_id,
        theme_id=item.theme_id,
        interaction_type="viewed",
        context_data=body.get("context_data", {}),
    )
    db.add(interaction)
    db.flush()

    # Update mastery via inference service
    inference_service.update_mastery_from_interaction(
        progress,
        interaction_type="seen_in_context",
        weight=body.get("weight", 0.5),
        context_data={"source": "self_study", "interaction_id": str(interaction.id)},
    )
    db.commit()

    # Get current level
    level = inference_service.get_level_classification(progress.mastery_level)

    return RecordInteractionResponse(
        interaction_id=interaction.id,
        mastery_level=round(progress.mastery_level, 2),
        level=level,
        message="Progreso actualizado correctamente",
    )


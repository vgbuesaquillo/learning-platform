from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, UUID as UUID_TYPE
from datetime import datetime, timezone
import asyncio
from pydantic import BaseModel, Field, EmailStr

from app.infrastructure.database import get_db
from app.core.dependencies import get_current_user, require_instructor, require_admin, require_own_resource
from app.domain.models import (
    User, LearningEvidence, Activity, UserProgress,
    Theme, LearningItem, UserInteraction # Import necessary models
)
from app.domain.schemas import (
    EvidenceCreate, EvidenceReview, EvidenceOut,
    LearningDashboard, NextLearningItemsResponse, RecordInteractionResponse, UserInteractionCreate
)
from app.core.knowledge_inference_service import KnowledgeInferenceService

router = APIRouter(prefix="/evidence", tags=["Evidence"])
progress_router = APIRouter(prefix="/progress", tags=["Progress"])

# --- Helper functions ---
def get_learning_item(db: Session, item_id: UUID_TYPE) -> LearningItem:
    db_item = db.query(LearningItem).filter(LearningItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning item not found")
    return db_item

def get_theme(db: Session, theme_id: UUID_TYPE) -> Theme:
    db_theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not db_theme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
    return db_theme

# --- Evidence Endpoints ---
@router.post("/", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def create_evidence(
    evidence_in: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records a new learning evidence (draft). User must be logged in."""
    activity = db.query(Activity).filter(Activity.id == evidence_in.activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    db_evidence = LearningEvidence(
        user_id=current_user.id,
        activity_id=evidence_in.activity_id,
        content=evidence_in.content,
        reflection=evidence_in.reflection,
        confidence_level=evidence_in.confidence_level,
        status="draft", # Default status
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    return EvidenceOut(**db_evidence.dict())

@router.post("/{evidence_id}/submit", response_model=EvidenceOut)
def submit_evidence(
    evidence_id: UUID_TYPE,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submits evidence for review. User must own the evidence."""
    evidence = db.query(LearningEvidence).filter(
        LearningEvidence.id == evidence_id,
        LearningEvidence.user_id == current_user.id,
    ).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if evidence.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only drafts can be submitted")

    evidence.status = "submitted"
    evidence.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(evidence)
    return EvidenceOut(**evidence.dict())

@router.post("/{evidence_id}/review", response_model=EvidenceOut)
def review_evidence(
    evidence_id: UUID_TYPE,
    body: EvidenceReview,
    db: Session = Depends(get_db),
    instructor: User = Depends(require_instructor), # Ensure user is an instructor
):
    """Instructor evaluates evidence and updates student's progress. Applies RBAC."""
    evidence = db.query(LearningEvidence).filter(LearningEvidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if evidence.status != "submitted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only submitted evidence can be reviewed")

    # --- Update Evidence with Evaluation ---
    evidence.score = body.score
    evidence.rubric_evaluation = body.rubric_evaluation
    evidence.qualitative_feedback = body.qualitative_feedback
    evidence.status = "approved"
    evidence.reviewed_at = datetime.now(timezone.utc)
    db.flush()

    # --- Update Progress using KnowledgeInferenceService ---
    activity = db.query(Activity).filter(Activity.id == evidence.activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated activity not found")

    # Infer Theme (defaulting to 'Inglés' or first active theme)
    active_theme = db.query(Theme).filter(Theme.name == "Inglés", Theme.is_active == True).first()
    if not active_theme:
        active_theme = db.query(Theme).filter(Theme.is_active == True).order_by(Theme.order).first()
        if not active_theme:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active theme found.")

    # Use NLP placeholder to find related LearningItems
    inference_service = KnowledgeInferenceService(db)
    related_items = inference_service.extract_learning_items_from_evidence(
        db=db,
        evidence_content=evidence.content,
        theme_id=active_theme.id,
        strategy="keyword_match"
    )

    if related_items:
        target_item = related_items[0]
        user_progress = db.query(UserProgress).filter(
            UserProgress.user_id == evidence.user_id,
            UserProgress.theme_id == active_theme.id,
            UserProgress.learning_item_id == target_item.id,
        ).first()

        if not user_progress:
            user_progress = UserProgress(
                user_id=evidence.user_id,
                theme_id=active_theme.id,
                learning_item_id=target_item.id,
                mastery_level=0.0,
                recurrence_score=0
            )
            db.add(user_progress)
            db.flush()

        inference_service.update_mastery_from_interaction(
            user_progress,
            interaction_type="evidence_approved",
            weight=float(evidence.score) / 100.0 if evidence.score is not None else 0.5,
            context_data={
                "evidence_id": str(evidence.id),
                "confidence_level": evidence.confidence_level,
                "qualitative_feedback": evidence.qualitative_feedback
            }
        )
        user_progress.last_practiced_at = datetime.now(timezone.utc)
        user_progress.history.append({
            "timestamp": user_progress.last_practiced_at.isoformat(),
            "type": "evidence_approved",
            "evidence_id": str(evidence.id),
            "new_mastery": user_progress.mastery_level,
            "score": evidence.score,
            "confidence": evidence.confidence_level,
            "triggered_by": "instructor_review"
        })
        db.flush()

    db.commit()
    db.refresh(evidence)
    return EvidenceOut(**evidence.dict())

@router.get("/my", response_model=List[EvidenceOut])
def my_evidences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all evidences submitted by the current user. Restricted to own data."""
    return [EvidenceOut(**e.dict()) for e in db.query(LearningEvidence).filter(
        LearningEvidence.user_id == current_user.id
    ).order_by(LearningEvidence.created_at.desc()).all()]

@router.get("/", response_model=List[EvidenceOut])
def get_all_evidences(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor), # Requires instructor role for global access
):
    """Get all evidences (instructors only)."""
    return [EvidenceOut(**e.dict()) for e in db.query(LearningEvidence)
            .order_by(LearningEvidence.created_at.desc()).all()]

# --- Progress Endpoints ---
# These are defined in progress.py and included in main.py
# Example: api_router.include_router(progress_router)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.infrastructure.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.domain.models import (
    User, LearningEvidence, Activity, CompetencyProgress,
    ActivityCompetency, EvidenceStatus, Enrollment,
    Theme, LearningItem, UserInteraction, UserProgress # Importar nuevos modelos
)
from app.domain.schemas import (
    EvidenceCreate, EvidenceReview, EvidenceOut,
    CompetencyProgressOut, LearningDashboard,
    UserProgressDetail, NextLearningItemsResponse, RecordInteractionResponse # Importar nuevos schemas de respuesta
)
# Importar el servicio de inferencia y configuraciones
from app.domain.services.knowledge_inference import KnowledgeInferenceService
from app.core.config import settings
from app.domain.models import Theme # Import Theme model for explicit use

router = APIRouter(prefix="/evidence", tags=["Evidence"])
progress_router = APIRouter(prefix="/progress", tags=["Progress"]) # Renombrado de /dashboard

# --- Helper to get an item by ID ---
def get_learning_item(db: Session, item_id: UUID) -> LearningItem:
    db_item = db.query(LearningItem).filter(LearningItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning item not found")
    return db_item

def get_theme(db: Session, theme_id: UUID) -> Theme:
    db_theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not db_theme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
    return db_theme

# --- CRUD Endpoints for Evidence ---
@router.post("/", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def create_evidence(
    evidence_in: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registrar una nueva evidencia de aprendizaje (borrador)."""
    activity = db.query(Activity).filter(Activity.id == evidence_in.activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    db_evidence = LearningEvidence(
        user_id=current_user.id,
        activity_id=evidence_in.activity_id,
        content=evidence_in.content,
        reflection=evidence_in.reflection,
        confidence_level=evidence_in.confidence_level,
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    return db_evidence

@router.post("/{evidence_id}/submit", response_model=EvidenceOut)
def submit_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enviar evidencia a revisión."""
    evidence = db.query(LearningEvidence).filter(
        LearningEvidence.id == evidence_id,
        LearningEvidence.user_id == current_user.id,
    ).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if evidence.status != EvidenceStatus.BORRADOR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only drafts can be submitted")

    evidence.status = EvidenceStatus.ENVIADA
    evidence.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(evidence)
    return evidence

@router.post("/{evidence_id}/review", response_model=EvidenceOut)
def review_evidence(
    evidence_id: UUID,
    body: EvidenceReview,
    db: Session = Depends(get_db),
    instructor: User = Depends(require_instructor),
):
    """Instructor evalúa una evidencia y actualiza el progreso del estudiante."""
    evidence = db.query(LearningEvidence).filter(LearningEvidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    # --- Update Evidence with Evaluation ---
    evidence.score = body.score
    evidence.rubric_evaluation = body.rubric_evaluation
    evidence.qualitative_feedback = body.qualitative_feedback
    evidence.status = EvidenceStatus.APROBADA
    evidence.reviewed_at = datetime.now(timezone.utc)
    db.flush()

    # --- Update Progress using KnowledgeInferenceService ---
    # This replaces the old competency-based progress update.
    # We need to determine the relevant LearningItems and Theme for this evidence.

    activity = db.query(Activity).filter(Activity.id == evidence.activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated activity not found for evidence")

    # Infer Theme (defaulting to 'Inglés' for MVP)
    active_theme = db.query(Theme).filter(Theme.name == "Inglés", Theme.is_active == True).first()
    if not active_theme:
        active_theme = db.query(Theme).filter(Theme.is_active == True).order_by(Theme.order).first()
        if not active_theme:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active theme found for progress update.")

    # --- Simulate finding relevant LearningItems ---
    related_items = db.query(LearningItem).filter(
        LearningItem.theme_id == active_theme.id,
        LearningItem.content.ilike(f"%{evidence.content.split()[0] if evidence.content else ''}%")
    ).limit(1).all()

    inference_service = KnowledgeInferenceService(db)

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
                recurrence_score=0,
            )
            db.add(user_progress)
            db.flush()

        inference_service.update_mastery_from_interaction(user_progress, {
            "interaction_type": "evidence_approved",
            "evidence_score": evidence.score,
            "confidence_level": evidence.confidence_level,
        })
        user_progress.last_practiced_at = datetime.now(timezone.utc)
        user_progress.history.append({
            "timestamp": user_progress.last_practiced_at.isoformat(),
            "type": "evidence_approved",
            "evidence_id": str(evidence.id),
            "new_mastery": user_progress.mastery_level
        })
        db.flush()

    db.commit()
    db.refresh(evidence)
    return evidence

@router.get("/my", response_model=List[EvidenceOut])
def my_evidences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all evidences submitted by the current user."""
    return db.query(LearningEvidence).filter(
        LearningEvidence.user_id == current_user.id
    ).order_by(LearningEvidence.created_at.desc()).all()

# --- Progress Endpoints ---
@progress_router.get("/dashboard/{_module_id}", response_model=LearningDashboard)
def get_dashboard(
    _module_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Displays the user's learning dashboard, including progress visualization
    (heatmap, level categories) based on LearningItems and inferred mastery.
    """
    # Determine the user's active theme, defaulting to 'Inglés'
    active_theme = db.query(Theme).filter(Theme.name == "Inglés", Theme.is_active == True).first()
    if not active_theme:
        active_theme = db.query(Theme).filter(Theme.is_active == True).order_by(Theme.order).first()
        if not active_theme:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active theme found.")

    inference_service = KnowledgeInferenceService(db)
    # Fetch progress records and generate dashboard data
    user_progress_records_for_theme = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.theme_id == active_theme.id
    ).all()

    # Create a list of item data including progress for heatmap/level calc
    items_with_progress_data = []
    if user_progress_records_for_theme:
        all_theme_items = db.query(LearningItem).filter(LearningItem.theme_id == active_theme.id).all()
        progress_map = {p.learning_item_id: p for p in user_progress_records_for_theme}
        for item in all_theme_items:
            progress = progress_map.get(item.id)
            if progress:
                items_with_progress_data.append({"item": item, "progress": progress})

    dashboard_data = inference_service.determine_level_and_heatmap(items_with_progress_data, active_theme.name)

    return LearningDashboard(
        user_id=current_user.id,
        module_id=_module_id, # Kept for API compatibility if needed
        module_title=f"Progreso en {active_theme.name}",
        overall_domain_score=dashboard_data.get("overall_theme_mastery_score", 0.0),
        highest_level_achieved="N/A", # Placeholder for LearningItems
        competencies_at_expert=0, # Placeholder
        total_evidences=0, # Placeholder
        approved_evidences=0, # Placeholder
        avg_confidence_vs_score=0.0, # Placeholder
        consistency_index=0.0, # Placeholder
        competency_breakdown=dashboard_data.get("heatmap", {}),
    )

@router.get("/next", response_model=NextLearningItemsResponse)
def get_next_learning_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetches the next set of learning items for the user to practice."""
    active_theme = db.query(Theme).filter(Theme.name == "Inglés", Theme.is_active == True).first()
    if not active_theme:
        active_theme = db.query(Theme).filter(Theme.is_active == True).order_by(Theme.order).first()
        if not active_theme:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active theme found.")

    inference_service = KnowledgeInferenceService(db)
    selected_items_data = inference_service.get_learning_items_for_practice(current_user.id, active_theme.id)

    return NextLearningItemsResponse(
        theme_id=active_theme.id,
        theme_name=active_theme.name,
        learning_items=[item_data["item"] for item_data in selected_items_data]
    )

@router.post("/interactions", response_model=RecordInteractionResponse, status_code=status.HTTP_201_CREATED)
def record_interaction(
    interaction: UserInteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Records a user interaction that can be used for knowledge inference."""
    learning_item = get_learning_item(db=db, item_id=interaction.learning_item_id)
    theme = get_theme(db=db, theme_id=interaction.theme_id)

    if learning_item.theme_id != interaction.theme_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Learning item and theme mismatch")

    db_interaction = UserInteraction(
        id=UUID(),
        user_id=current_user.id,
        learning_item_id=interaction.learning_item_id,
        theme_id=interaction.theme_id,
        interaction_type=interaction.interaction_type,
        context_data=interaction.context_data,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)

    # --- Update UserProgress based on this interaction ---
    user_progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.theme_id == interaction.theme_id,
        UserProgress.learning_item_id == interaction.learning_item_id
    ).first()

    if not user_progress:
        user_progress = UserProgress(
            user_id=current_user.id,
            theme_id=interaction.theme_id,
            learning_item_id=interaction.learning_item_id,
            mastery_level=0.0,
            recurrence_score=0
        )
        db.add(user_progress)
        db.flush()

    inference_service = KnowledgeInferenceService(db)
    inference_service.update_mastery_from_interaction(user_progress, {
        "interaction_type": interaction.interaction_type,
        "context_data": interaction.context_data
    })

    db.commit()
    return RecordInteractionResponse(interaction_id=db_interaction.id)

# --- Register routers ---
# These should be included in the main FastAPI app (e.g., in main.py)
# Example: app.include_router(router, prefix="/api")
# Example: app.include_router(progress_router, prefix="/api")

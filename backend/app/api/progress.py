from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID as UUID_TYPE
from datetime import datetime, timezone

from app.infrastructure.database import get_db
from app.core.dependencies import get_current_user, require_instructor, require_own_resource # Import new dependencies
from app.domain.models import User, UserProgress, LearningItem, Theme, LearningEvidence
from app.domain.schemas import LearningDashboard, NextLearningItemsResponse, ThemesProgressResponse, ThemeProgressSummary # Import relevant schemas
from app.domain.services.knowledge_inference import KnowledgeInferenceService

router = APIRouter(prefix="/progress", tags=["Progress"])

# --- Helper to get active theme ---
def get_active_theme(db: Session) -> Theme:
    """Fetches the first active theme."""
    active_theme = db.query(Theme).filter(Theme.is_active == True).order_by(Theme.order).first()
    if not active_theme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active theme found.")
    return active_theme

# --- Progress Endpoints ---
@router.get("/dashboard/{_module_id}", response_model=LearningDashboard)
def get_user_dashboard(
    _module_id: UUID_TYPE, # Parameter kept for API compatibility, might be redundant.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # Ensure user is logged in
):
    """
    Displays the user's learning dashboard for the active theme.
    Restricted using RBAC to ensure users only see their own data unless they are instructors.
    """
    active_theme = get_active_theme(db)

    # Apply RBAC: Ensure user can only view their own dashboard unless they are an instructor.
    # For instructors, this check would need to be more complex (e.g., identifying whose dashboard).
    # For now, we assume it's primarily for the logged-in user's own data.
    # If instructors should see others, a different dependency or check is needed.
    # The get_current_user already provides the logged-in user.
    # For instructors, the `require_instructor` dependency would be used if direct access to others' dashboards is enabled.
    # For now, we continue fetching data for the `current_user`.

    inference_service = KnowledgeInferenceService(db)
    # Fetch progress records for the current user and the active theme
    user_progress_records_for_theme = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.theme_id == active_theme.id
    ).all()

    # Prepare data for dashboard computation
    items_with_progress_data = []
    if user_progress_records_for_theme:
        all_theme_items = db.query(LearningItem).filter(LearningItem.theme_id == active_theme.id).all()
        progress_map = {p.learning_item_id: p for p in user_progress_records_for_theme}
        for item in all_theme_items:
            progress = progress_map.get(item.id)
            if progress:
                items_with_progress_data.append({"item": item, "progress": progress})
            else:
                # Create a default progress record for items without interaction yet
                default_progress = UserProgress(
                    user_id=current_user.id,
                    theme_id=active_theme.id,
                    learning_item_id=item.id,
                    mastery_level=0.0,
                    recurrence_score=0,
                    history=[]
                )
                items_with_progress_data.append({"item": item, "progress": default_progress})

    # Placeholder for actual dashboard data generation logic in KnowledgeInferenceService
    # This method needs to be implemented in KnowledgeInferenceService
    dashboard_data = inference_service.determine_level_and_heatmap(items_with_progress_data, active_theme.name)

    # Construct the LearningDashboard response
    # Ensure counts are accurately aggregated. Using placeholder counts for now.
    total_evidences = db.query(LearningEvidence).filter(
        LearningEvidence.user_id == current_user.id,
        LearningEvidence.status.in_(['approved', 'submitted'])
    ).count()
    approved_evidences = db.query(LearningEvidence).filter(
        LearningEvidence.user_id == current_user.id,
        LearningEvidence.status == "approved"
    ).count()

    return LearningDashboard(
        user_id=current_user.id,
        module_id=_module_id,
        module_title=f"Learning Dashboard for {active_theme.name}",
        overall_domain_score=dashboard_data.get("overall_theme_mastery_score", 0.0),
        highest_level_achieved=dashboard_data.get("highest_level_achieved", "N/A"),
        competencies_at_expert=dashboard_data.get("competencies_at_expert", 0),
        total_evidences=total_evidences,
        approved_evidences=approved_evidences,
        avg_confidence_vs_score=dashboard_data.get("avg_confidence_vs_score", 0.0),
        consistency_index=dashboard_data.get("consistency_index", 0.0),
        competency_breakdown=dashboard_data.get("heatmap", []),
    )

@router.get("/next", response_model=NextLearningItemsResponse)
def get_next_learning_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetches the next set of learning items for the user to practice."""
    active_theme = get_active_theme(db)

    # RBAC: Access to next items is generally per-user. Instructors might have a broader view option.
    # For now, we fetch for the current_user.

    inference_service = KnowledgeInferenceService(db)
    try:
        selected_items_data = inference_service.get_learning_items_for_practice(current_user.id, active_theme.id)
    except NotImplementedError:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="get_learning_items_for_practice method not implemented yet.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching next learning items: {str(e)}")

    return NextLearningItemsResponse(
        theme_id=active_theme.id,
        theme_name=active_theme.name,
        learning_items=[item_data["item"] for item_data in selected_items_data] # Assumes item_data is a dict with 'item' key
    )

@router.get("/themes", response_model=ThemesProgressResponse)
def get_themes_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns progress summary for all themes for the current user."""
    themes = db.query(Theme).filter(Theme.is_active == True).order_by(Theme.order).all()
    inference_service = KnowledgeInferenceService(db)
    summaries = []

    for theme in themes:
        items = db.query(LearningItem).filter(LearningItem.theme_id == theme.id).all()
        total_items = len(items)

        progresses = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.theme_id == theme.id,
        ).all()

        progress_map = {p.learning_item_id: p for p in progresses}
        completed_items = sum(1 for p in progresses if p.mastery_level >= 0.6)

        if total_items > 0 and progresses:
            total_mastery = sum(p.mastery_level for p in progresses)
            overall_mastery = total_mastery / total_items
        else:
            overall_mastery = 0.0

        level = inference_service.get_level_classification(overall_mastery)

        summaries.append(ThemeProgressSummary(
            theme_id=theme.id,
            theme_name=theme.name,
            theme_order=theme.order,
            total_items=total_items,
            completed_items=completed_items,
            overall_mastery=round(overall_mastery, 2),
            level=level,
        ))

    return ThemesProgressResponse(themes=summaries)


# Note: The record_interaction endpoint is part of evidence.py's router, not progress.py
# It's used to trigger updates to UserProgress based on actions.

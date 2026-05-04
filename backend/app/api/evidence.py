from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from app.infrastructure.database import get_db
from app.core.dependencies import get_current_user, require_instructor
from app.domain.models import (
    User, LearningEvidence, Activity, CompetencyProgress,
    ActivityCompetency, EvidenceStatus, Enrollment
)
from app.domain.schemas import (
    EvidenceCreate, EvidenceReview, EvidenceOut,
    CompetencyProgressOut, LearningDashboard
)
from app.domain.services.progress_calculator import (
    update_competency_progress, calculate_metacognitive_gap,
    LEVEL_ORDER
)

router = APIRouter(prefix="/evidence", tags=["Evidencias"])
progress_router = APIRouter(prefix="/progress", tags=["Progreso"])


# ── Evidencias ─────────────────────────────────────────────────────────────

@router.post("/", response_model=EvidenceOut, status_code=201)
def create_evidence(
    body: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registrar una nueva evidencia de aprendizaje (borrador)."""
    activity = db.query(Activity).filter(Activity.id == body.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    evidence = LearningEvidence(
        user_id=current_user.id,
        activity_id=body.activity_id,
        content=body.content,
        reflection=body.reflection,
        confidence_level=body.confidence_level,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


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
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    if evidence.status != EvidenceStatus.BORRADOR:
        raise HTTPException(status_code=400, detail="Solo se pueden enviar borradores")

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
    evidence = db.query(LearningEvidence).filter(
        LearningEvidence.id == evidence_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    # Guardar evaluación
    evidence.score = body.score
    evidence.rubric_evaluation = body.rubric_evaluation
    evidence.qualitative_feedback = body.qualitative_feedback
    evidence.status = EvidenceStatus.APROBADA
    evidence.reviewed_at = datetime.now(timezone.utc)
    db.flush()

    # Actualizar progreso por competencia
    activity_competencies = db.query(ActivityCompetency).filter(
        ActivityCompetency.activity_id == evidence.activity_id
    ).all()

    for ac in activity_competencies:
        progress = db.query(CompetencyProgress).filter(
            CompetencyProgress.user_id == evidence.user_id,
            CompetencyProgress.competency_id == ac.competency_id,
        ).first()

        if not progress:
            progress = CompetencyProgress(
                user_id=evidence.user_id,
                competency_id=ac.competency_id,
            )
            db.add(progress)
            db.flush()

        update_competency_progress(progress, evidence)

    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/my", response_model=List[EvidenceOut])
def my_evidences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(LearningEvidence).filter(
        LearningEvidence.user_id == current_user.id
    ).order_by(LearningEvidence.created_at.desc()).all()


# ── Dashboard de progreso real ─────────────────────────────────────────────

@progress_router.get("/dashboard/{module_id}", response_model=LearningDashboard)
def get_dashboard(
    module_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard de aprendizaje real:
    - Dominio por competencia (no solo %)
    - Nivel alcanzado (Novato → Experto)
    - Consistencia, brecha metacognitiva, evolución
    """
    from app.domain.models import LearningModule, Competency

    module = db.query(LearningModule).filter(LearningModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    # Todas las evidencias del usuario en este módulo
    evidences = (
        db.query(LearningEvidence)
        .join(Activity, LearningEvidence.activity_id == Activity.id)
        .filter(
            LearningEvidence.user_id == current_user.id,
            Activity.module_id == module_id,
        )
        .all()
    )

    # Progreso por competencia
    competency_progress = (
        db.query(CompetencyProgress, Competency)
        .join(Competency, CompetencyProgress.competency_id == Competency.id)
        .filter(
            CompetencyProgress.user_id == current_user.id,
            Competency.module_id == module_id,
        )
        .all()
    )

    # Construir breakdown
    breakdown = []
    for cp, comp in competency_progress:
        breakdown.append(CompetencyProgressOut(
            competency_id=cp.competency_id,
            competency_name=comp.name,
            current_level=cp.current_level,
            domain_score=cp.domain_score,
            consistency_score=cp.consistency_score,
            evidence_count=cp.evidence_count,
            last_evidence_at=cp.last_evidence_at,
            history=cp.history or [],
        ))

    # Métricas globales
    approved = [e for e in evidences if e.status == EvidenceStatus.APROBADA]
    domain_scores = [cp.domain_score for cp, _ in competency_progress]
    overall = sum(domain_scores) / len(domain_scores) if domain_scores else 0.0

    levels_achieved = [cp.current_level for cp, _ in competency_progress]
    highest = max(
        (LEVEL_ORDER.index(l) for l in levels_achieved),
        default=0
    )
    highest_level = LEVEL_ORDER[highest]

    from app.domain.models import DomainLevel
    expert_count = sum(1 for cp, _ in competency_progress if cp.current_level == DomainLevel.EXPERTO)
    metacog_gap = calculate_metacognitive_gap(evidences)
    consistency = sum(cp.consistency_score for cp, _ in competency_progress) / max(len(competency_progress), 1)

    return LearningDashboard(
        user_id=current_user.id,
        module_id=module_id,
        module_title=module.title,
        overall_domain_score=round(overall, 2),
        highest_level_achieved=highest_level,
        competencies_at_expert=expert_count,
        total_evidences=len(evidences),
        approved_evidences=len(approved),
        avg_confidence_vs_score=round(metacog_gap, 2),
        consistency_index=round(consistency, 2),
        competency_breakdown=breakdown,
    )

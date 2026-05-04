"""
ProgressCalculator — núcleo del sistema de medición de aprendizaje real.

Calcula métricas más allá del porcentaje de avance:
- Nivel de dominio por competencia
- Consistencia entre evidencias
- Brecha metacognitiva (confianza vs score real)
- Evolución temporal
"""
from typing import List, Optional
from datetime import datetime, timezone
from app.domain.models import (
    LearningEvidence, CompetencyProgress,
    DomainLevel, EvidenceStatus
)


LEVEL_THRESHOLDS = {
    DomainLevel.NOVATO: (0, 40),
    DomainLevel.INTERMEDIO: (40, 65),
    DomainLevel.COMPETENTE: (65, 85),
    DomainLevel.EXPERTO: (85, 100),
}

LEVEL_ORDER = [
    DomainLevel.NOVATO,
    DomainLevel.INTERMEDIO,
    DomainLevel.COMPETENTE,
    DomainLevel.EXPERTO,
]


def score_to_level(score: float) -> DomainLevel:
    for level, (low, high) in LEVEL_THRESHOLDS.items():
        if low <= score < high:
            return level
    return DomainLevel.EXPERTO


def calculate_consistency(scores: List[float]) -> float:
    """
    Mide la consistencia entre evidencias.
    Alta consistencia = el estudiante demuestra dominio de forma sostenida.
    Baja consistencia = desempeño errático.
    Returns 0-100.
    """
    if len(scores) < 2:
        return 100.0 if scores else 0.0
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5
    # Penalizar desviación estándar alta (máx penalización a std=30)
    consistency = max(0.0, 100.0 - (std_dev / 30.0) * 100.0)
    return round(consistency, 2)


def calculate_metacognitive_gap(evidences: List[LearningEvidence]) -> float:
    """
    Brecha metacognitiva: diferencia entre confianza declarada y score real.
    Cercano a 0 = buena calibración. Positivo = sobreconfianza. Negativo = infraconfianza.
    """
    paired = [
        (e.confidence_level, e.score)
        for e in evidences
        if e.confidence_level is not None and e.score is not None
    ]
    if not paired:
        return 0.0

    gaps = []
    for confidence, score in paired:
        # Normalizar confianza (1-5) a escala 0-100
        confidence_normalized = (confidence - 1) / 4 * 100
        gaps.append(confidence_normalized - score)

    return round(sum(gaps) / len(gaps), 2)


def update_competency_progress(
    progress: CompetencyProgress,
    new_evidence: LearningEvidence,
) -> CompetencyProgress:
    """
    Actualiza el progreso de una competencia tras evaluar una nueva evidencia.
    Usa promedio ponderado exponencial para dar más peso a evidencias recientes.
    """
    if new_evidence.score is None:
        return progress

    alpha = 0.4  # Factor de decaimiento: 0=sin memoria, 1=solo última evidencia

    # Score acumulado con media ponderada exponencial
    if progress.evidence_count == 0:
        new_domain_score = new_evidence.score
    else:
        new_domain_score = (
            alpha * new_evidence.score + (1 - alpha) * progress.domain_score
        )

    # Actualizar historial
    history_entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        "score": round(new_evidence.score, 2),
        "domain_score": round(new_domain_score, 2),
        "level": score_to_level(new_domain_score).value,
    }
    history = list(progress.history or [])
    history.append(history_entry)

    # Calcular consistencia con las últimas 10 evidencias
    recent_scores = [h["score"] for h in history[-10:]]

    progress.domain_score = round(new_domain_score, 2)
    progress.current_level = score_to_level(new_domain_score)
    progress.consistency_score = calculate_consistency(recent_scores)
    progress.evidence_count += 1
    progress.last_evidence_at = datetime.now(timezone.utc)
    progress.history = history

    return progress

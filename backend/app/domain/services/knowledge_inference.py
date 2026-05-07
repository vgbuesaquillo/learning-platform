from sqlalchemy.orm import Session
from app.domain.models import UserProgress, LearningItem
from app.core.config import settings
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger()

# Constants, could be moved to settings if needed for finer control
MASTERY_DECAY_PER_WEEK_DEFAULT = 0.01  # 1% per week
MAX_USAGE_WEIGHTING = 5.0  # Max weight for an item interaction
MAX_MASTER_LEVEL = 1.0
MIN_MASTER_LEVEL = 0.0
MAX_CONFIDENCE = 5.0
METACOG_GAP_WEIGHT_FACTOR = 0.2 # How much confidence impacts mastery

class KnowledgeInferenceService:
    def __init__(self, db: Session):
        self.db = db

    def apply_forgetting_decay(self, record: UserProgress):
        """
        Applies forgetting decay to a UserProgress record.
        Calculates decay based on time since last practice and updates mastery level
        and recurrence score.
        """
        if record.last_practiced_at is None:
            # If never practiced, apply decay based on creation date
            # Ensure it has at least decayed from max, if created long ago
            if record.created_at < datetime.now(timezone.utc) - timedelta(weeks=1):
                 weeks_since_creation = (datetime.now(timezone.utc) - record.created_at).days / 7
                 decay_amount = min(weeks_since_creation * self._get_decay_rate(), MAX_MASTER_LEVEL)
                 record.mastery_level = max(MIN_MASTER_LEVEL, MAX_MASTER_LEVEL - decay_amount)
            else: # If created recently, assume initial mastery is high and no decay yet
                 record.mastery_level = MAX_MASTER_LEVEL # Default to max mastery if never practiced and recently created
        else:
            weeks_since_practice = (datetime.now(timezone.utc) - record.last_practiced_at).days / 7
            # Apply decay only if practiced more than a week ago
            if weeks_since_practice > 1.0:
                decay_amount = min(weeks_since_practice * self._get_decay_rate(), MAX_MASTER_LEVEL) # Cap decay at MAX_MASTER_LEVEL
                record.mastery_level = max(MIN_MASTER_LEVEL, record.mastery_level - decay_amount)

        # Recurrence score logic
        # This logic might need refinement - current assumption: higher recurrence needs more practice
        # Simple approach: increase score based on time since practice, decrease upon successful practice
        if record.last_practiced_at is None:
            # If never practiced, increase recurrence score by a fixed amount for being "forgotten"
             record.recurrence_score += self._get_recurrence_increase_per_week()
        else:
            # If practiced, but decay applied, it implies some forgetting.
            # The actual practice history is crucial here, not just decay.
            # For now, we'll just increase recurrence a bit if decay was applied because it's old.
            if weeks_since_practice > 1.0:
                record.recurrence_score += self._get_recurrence_increase_per_week()

        # --- History Logging ---
        # Add record of this decay application to history
        history_entry = {
            "type": "decay", # Mark this as a scheduled job decay
            "mastery_level_before": record.mastery_level + (weeks_since_practice * self._get_decay_rate() if weeks_since_practice > 1.0 and record.last_practiced_at else 0), # approximate before value
            "mastery_level_after": record.mastery_level,
            "recurrence_score_before": record.recurrence_score - self._get_recurrence_increase_per_week() if weeks_since_practice > 1.0 and record.last_practiced_at else record.recurrence_score,
            "recurrence_score_after": record.recurrence_score,
            "decay_weeks": round(weeks_since_practice, 2) if weeks_since_practice > 1.0 and record.last_practiced_at else ( (datetime.now(timezone.utc) - record.created_at).days / 7 if record.last_practiced_at is None and record.created_at else 0.0 ),
            "timestamp": datetime.now(timezone.utc),
            "triggered_by": "scheduled_job" # Distinct from manual calls
        }
        if record.history is None:
            record.history = []
        record.history.append(history_entry)

        # Ensure mastery is within bounds after all updates
        record.mastery_level = max(MIN_MASTER_LEVEL, min(MAX_MASTER_LEVEL, record.mastery_level))

        logger.debug("applied_forgetting_decay", record_id=str(record.id), mastery=record.mastery_level, recurrence=record.recurrence_score, weeks=history_entry["decay_weeks"])


    def get_level_classification(self, mastery_level: float) -> str:
        """Classifies mastery level into categories (e.g., Novice, Intermediate)."""
        if mastery_level < 0.4:
            return "Novice"
        elif mastery_level < 0.65:
            return "Intermediate"
        elif mastery_level < 0.85:
            return "Competent"
        else:
            return "Expert"

    def calculate_consistency_score(self, record: UserProgress) -> float:
        """Calculates consistency based on the history of interactions."""
        # Placeholder: implement logic to analyze 'history' for consistency
        # Example: std dev of mastery levels over recent interactions.
        # For now, return a dummy value.
        return 0.0 # Placeholder

    def calculate_metacognitive_gap(self, student_confidence: float, actual_mastery: float) -> float:
        """Calculates metacognitive gap based on confidence vs actual mastery."""
        # Confidence is on a scale of 1-5
        # Normalize confidence to 0-1 scale
        normalized_confidence = (student_confidence - 1.0) / (MAX_CONFIDENCE - 1.0)
        gap = abs(normalized_confidence - actual_mastery)
        return gap * METACOG_GAP_WEIGHT_FACTOR # Scale the gap impact

    def _get_decay_rate(self) -> float:
        """Retrieves the decay rate per week, falling back to default if not set."""
        return getattr(settings, 'DECAY_RATE_PER_WEEK', MASTERY_DECAY_PER_WEEK_DEFAULT)

    def _get_recurrence_increase_per_week(self) -> int:
        """Retrieves the recurrence score increase per week."""
        return getattr(settings, 'DECAY_RECURRENCE_INCREASE_PER_WEEK', 1)

    def extract_learning_items_from_evidence(
        self,
        db: Session,
        evidence_content: str,
        theme_id: UUID,
        strategy: str = "keyword_match"   # Parametro para futuro NLP real
    ) -> List[LearningItem]:
        """
        Placeholder NLP: extracts LearningItems related to evidence content.

        Current Strategy (MVP): keyword matching of the first few words of the content.
        Future Strategy: semantic embeddings (e.g., sentence-transformers).

        Args:
            strategy: "keyword_match" (MVP) | "semantic" (future)
        """
        if strategy == "keyword_match":
            # Extract meaningful tokens (more robust than just the first word)
            tokens = [
                w.strip(".,!?;:").lower()
                for w in evidence_content.split()[:5] # Consider first 5 words
                if len(w) > 3  # Ignore very short words
            ]
            if not tokens:
                return []

            # Query for items matching any of the tokens in their content
            # Using ILIKE for case-insensitive search
            query = db.query(LearningItem).filter(LearningItem.theme_id == theme_id)

            # Build conditions for tokens
            conditions = [LearningItem.content.ilike(f"%{token}%") for token in tokens]

            if conditions:
                # Use OR to combine conditions
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))

            items = query.limit(3).all() # Get up to 3 related items
            return items

        # Placeholder for future implementations (e.g., semantic search)
        return [] # Return empty list if strategy is not keyword_match or not implemented


    def update_mastery_from_interaction(self, record: UserProgress, interaction_type: str, weight: float, context_data: Dict[str, Any] = None):
        """
        Updates mastery level based on user interaction with a learning item.
        """
        if context_data is None:
            context_data = {}

        # Determine weight based on interaction type - Example values
        interaction_weights = {
            "used_in_sentence": 1.5,
            "spoken_correctly": 2.5,
            "correctly_identified": 2.0,
            "seen_in_context": 1.0,
        }

        actual_weight = weight if weight > 0 else interaction_weights.get(interaction_type, 1.0)

        if actual_weight > MAX_USAGE_WEIGHTING:
            actual_weight = MAX_USAGE_WEIGHTING

        mastery_gain_potential = (actual_weight / MAX_USAGE_WEIGHTING)
        gain_multiplier = (1.0 - record.mastery_level * 0.75)
        mastery_gain = mastery_gain_potential * gain_multiplier

        record.mastery_level += mastery_gain
        record.mastery_level = max(MIN_MASTER_LEVEL, min(MAX_MASTER_LEVEL, record.mastery_level))

        record.recurrence_score = max(0, record.recurrence_score - int(actual_weight * 1.5))
        record.last_practiced_at = datetime.now(timezone.utc)

        history_entry = {
            "type": "interaction",
            "interaction_type": interaction_type,
            "weight": actual_weight,
            "mastery_level_before": record.mastery_level - mastery_gain,
            "mastery_level_after": record.mastery_level,
            "recurrence_score_before": record.recurrence_score + int(actual_weight * 1.5),
            "recurrence_score_after": record.recurrence_score,
            "context_data": context_data,
            "timestamp": datetime.now(timezone.utc)
        }
        if record.history is None:
            record.history = []
        record.history.append(history_entry)

        logger.debug("updated_mastery_from_interaction", record_id=str(record.id), mastery=record.mastery_level, recurrence=record.recurrence_score, type=interaction_type)

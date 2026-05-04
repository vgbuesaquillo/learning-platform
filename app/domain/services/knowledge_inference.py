# app/domain/services/knowledge_inference.py

import datetime
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.models import (
    UserProgress,
    LearningItem,
    UserInteraction,
    Theme,
    User # Assuming User model is needed for context, though not directly used in static methods
)
from app.core.config import settings # For general configurations like decay rates

# --- Constants and Configuration ---
# These could also be loaded from settings or database for more flexibility.

# Weighting for different interaction types. Higher weight means stronger positive impact on mastery.
# These are initial estimates and can be tuned.
INTERACTION_WEIGHTS = {
    "used_in_sentence": 1.5,          # Using a word/phrase in a sentence
    "written_correctly": 2.0,         # Writing it correctly in a response/exercise
    "identified_in_context": 1.0,     # Identifying it correctly in a given context (e.g., reading)
    "spoken_correctly": 2.5,          # Speaking it correctly (if voice input is enabled)
    "identified_in_audio": 1.2,       # Identifying it in audio
    # Add more types as needed
}

# Maximum usage count considered for initial mastery gain (e.g., reaching peak learning effect)
MAX_USAGE_WEIGHTING = 5 # Based on user's "five uses as maximum weighting"

# Mastery level threshold for an item to be considered "mastered"
MASTERY_APPROVED_THRESHOLD = 0.8

# Decay rate for mastery_level per week of inactivity
MASTERY_DECAY_PER_WEEK = 0.01 # 1% per week, as discussed

# How recurrence score increases when an item is not practiced (e.g., per week)
RECURRENCE_SCORE_INCREASE_PER_WEEK = 1

# --- Knowledge Inference Service ---

class KnowledgeInferenceService:

    def __init__(self, db: Session):
        self.db = db

    def update_mastery_from_interaction(self, user_progress: UserProgress, interaction_data: Dict[str, Any]):
        """
        Updates user_progress mastery_level based on a single interaction.
        This method should be called AFTER a UserInteraction record is created.
        It analyzes the interaction and applies its impact on mastery.
        """
        interaction_type = interaction_data.get("interaction_type")
        # The interaction_data would typically come from the UserInteraction object saved in DB
        # For simulation purposes, we might pass relevant parts.

        weight = INTERACTION_WEIGHTS.get(interaction_type, 0.5) # Default weight if type is unknown

        # Simple mastery increase logic: apply weight directly or proportionally
        # A more complex model could consider context_data, evidence score, etc.
        #
        # Example: Mastery increases based on weight, capped by MAX_USAGE_WEIGHTING effect.
        # New items start with 0 mastery.

        # If mastery_level is already high, further increases might be smaller.
        # For now, a simple additive model.

        mastery_gain = weight / MAX_USAGE_WEIGHTING # Normalize gain based on max usage effect
        user_progress.mastery_level = min(1.0, user_progress.mastery_level + mastery_gain)

        # Recurrence score usually decreases with practice or stays low if mastery is gained.
        # When an item is practiced successfully, its recurrence need might decrease.
        # For simplicity, we'll make recurrence_score decrease slightly here.
        user_progress.recurrence_score = max(0, user_progress.recurrence_score - 1) # Reduce recurrence need

        user_progress.last_practiced_at = datetime.datetime.now(datetime.timezone.utc)

        # Add to history (simplified)
        user_progress.history.append({
            "timestamp": user_progress.last_practiced_at.isoformat(),
            "type": interaction_type,
            "mastery_change": mastery_gain,
            "new_mastery": user_progress.mastery_level
        })

        self.db.flush()


    def apply_forgetting_decay(self, user_progress: UserProgress):
        """
        Applies decay to mastery_level if the item hasn't been practiced recently.
        Also increases recurrence_score.
        """
        if user_progress.last_practiced_at:
            now = datetime.datetime.now(datetime.timezone.utc)
            weeks_since_practice = (now - user_progress.last_practiced_at).days / 7

            if weeks_since_practice >= 1: # Apply decay weekly
                decay_amount = MASTERY_DECAY_PER_WEEK * weeks_since_practice
                user_progress.mastery_level = max(0.0, user_progress.mastery_level - decay_amount)

                # Increase recurrence score for items that are not being practiced/mastered
                user_progress.recurrence_score += int(weeks_since_practice) * RECURRENCE_SCORE_INCREASE_PER_WEEK

                user_progress.history.append({
                    "timestamp": now.isoformat(),
                    "type": "decay",
                    "mastery_change": -decay_amount,
                    "new_mastery": user_progress.mastery_level,
                    "recurrence_change": int(weeks_since_practice) * RECURRENCE_SCORE_INCREASE_PER_WEEK
                })
        else:
            # If never practiced, increase recurrence score over time
            # This calculation depends on how often this function is called.
            # If called daily, it will accumulate faster. Let's assume weekly context.
            user_progress.recurrence_score += RECURRENCE_SCORE_INCREASE_PER_WEEK # Add score for initial lack of practice

        self.db.flush()

    def get_learning_items_for_practice(self, user_id: UUID, theme_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Determines which learning items should be presented next for practice.
        Prioritizes items with lower mastery and/or higher recurrence score.
        """
        # Fetch user's progress for the given theme
        user_progress_records = self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.theme_id == theme_id
        ).all()

        # Fetch all learning items for the theme
        all_theme_items = self.db.query(LearningItem).filter(LearningItem.theme_id == theme_id).all()

        # Map progress by learning_item_id for quick lookup
        progress_map = {p.learning_item_id: p for p in user_progress_records}

        items_with_progress_data = []

        # Process items already in user_progress
        for item in all_theme_items:
            progress = progress_map.get(item.id)
            if progress:
                items_with_progress_data.append({
                    "item": item,
                    "progress": progress
                })
            else:
                # Item exists but user has no progress record for it yet (treat as new)
                items_with_progress_data.append({
                    "item": item,
                    "progress": None # Indicates a new item for this user/theme
                })

        # Sort items:
        # 1. Prioritize items not yet practiced (None progress)
        # 2. Then, prioritize items with lower recurrence_score
        # 3. Then, prioritize items with lower mastery_level
        items_with_progress_data.sort(key=lambda x: (
            x["progress"] is None, # True comes first (new items)
            x["progress"].recurrence_score if x["progress"] else float('inf'), # Lower recurrence first
            x["progress"].mastery_level if x["progress"] else 0.0 # Lower mastery first
        ))

        # Apply forgetting decay to items that have been practiced but not recently
        # This decay is applied conceptually here to influence sorting/selection.
        # A batch job or on-demand update would permanently alter DB values.
        # For selection, we can 'simulate' decay for sorting if last_practiced_at is far in past.

        # To simplify for now, we'll rely on recurrence_score and mastery_level as updated periodically.
        # A background task or hook would be responsible for 'applying_forgetting_decay' to the DB.
        # For real-time selection, we can just use the current values.

        # Select the top N items for practice
        selected_items_for_practice = items_with_progress_data[:limit]

        # Return in a format suitable for the frontend response (e.g., NextLearningItemsResponse structure)
        return selected_items_for_practice

    def determine_level_and_heatmap(
        self,
        user_progress_list: List[Dict[str, Any]],
        theme_name: str
    ) -> Dict[str, Any]:
        """
        Generates data for heatmap and level representation based on user progress.
        Placeholder for level mapping (A, B, C).
        """
        heatmap_data = {}
        level_metrics = {} # Placeholder for level data like 'A1': mastery_avg, 'A2': mastery_avg, etc.

        if not user_progress_list:
            return {"heatmap": {}, "levels": {}}

        # Simple mapping for overall level based on average mastery across the theme
        # This is a very basic heuristic and would need refinement.
        # Example: A, B, C levels mapped to mastery thresholds.
        # Currently, maps to general theme progress.
        all_masteries = [item_data["progress"].mastery_level for item_data in user_progress_list if item_data["progress"]]
        average_mastery = sum(all_masteries) / len(all_masteries) if all_masteries else 0.0

        # Translate average mastery to approximate CEFR levels for theme (Very Basic)
        # This is a simplified mapping. Real CEFR mapping is more complex.
        if average_mastery < 0.3:
            current_level_category = "A1 (Novato)"
        elif average_mastery < 0.5:
            current_level_category = "A2 (Básico)"
        elif average_mastery < 0.7:
            current_level_category = "B1 (Intermedio)"
        elif average_mastery < 0.9:
            current_level_category = "B2 (Intermedio Alto)"
        else:
            current_level_category = "C1 (Avanzado)"

        level_metrics = {
            "current_level_category": current_level_category,
            "overall_theme_mastery": round(average_mastery, 2)
        }

        # Generate heatmap data
        for item_data in user_progress_list:
            item = item_data["item"]
            progress = item_data["progress"]

            if progress:
                # 'Heat' is high if mastery is high and recurrence score is low (recently practiced)
                # 'Cold' if mastery is low and recurrence score is high (forgotten/needs practice)
                # Using mastery level and recurrence_score to create a 'heat' value.
                # Higher score means 'colder' or needs more practice.
                # Low mastery = Cold, High mastery = Warm/Hot.
                # Recurrence Score: High = Cold (needs practice), Low = Warm/Hot (recent/mastered)

                # Heatmap color/value logic:
                # Value range for heatmap could be 0 (coldest) to 1 (hottest/clearest)
                # Let's say:
                # - Hot/Clear: High mastery AND low recurrence_score
                # - Cold/Dark: Low mastery OR high recurrence_score

                # Example heuristic:
                # Heat = mastery_level * (1 - normalized_recurrence_score)
                # Need to normalize recurrence_score to a 0-1 range. If max recurrence is say - 20 weeks * 1 point/week = 20.
                # Let's assume a max recurrence score of 20 for normalization.
                max_expected_recurrence_score = 20 # This should be configurable or dynamically derived
                normalized_recurrence = min(progress.recurrence_score, max_expected_recurrence_score) / max_expected_recurrence_score

                # Inverse relationship with recurrence: lower score = hotter
                heat_value = progress.mastery_level * (1.0 - normalized_recurrence)
                # Ensure values are within 0-1 range
                heat_value = max(0.0, min(1.0, heat_value))

                heatmap_data[str(item.id)] = { # Use item ID as key for heatmap rendering
                    "content": item.content,
                    "item_type": item.item_type,
                    "heat": round(heat_value, 2), # Heat value 0 (cold) to 1 (hot)
                    "mastery_level": round(progress.mastery_level, 2),
                    "recurrence_score": progress.recurrence_score
                }

        return {"heatmap": heatmap_data, "levels": level_metrics}

    # --- Static Methods for Singleton-like access ---
    # This pattern might be useful if the service has shared state or configuration
    # that needs to be initialized once per session or globally.
    # For now, we assume it's instantiated with a DB session.

    @staticmethod
    def get_instance(db: Session):
        return KnowledgeInferenceService(db)

# --- Helper Functions (potentially used by API endpoints or service) ---

def update_progress_from_evidence(db: Session, evidence: UserInteraction, user_id: UUID, theme_id: UUID):
    """
    This function would be called when an evidence is reviewed/approved.
    It's more complex than simple interactions as it involves evaluating a body of work.
    It needs to identify relevant LearningItems within the evidence content or linked activity.
    """
    # Placeholder: This part needs significant development.
    # It's crucial for linking 'approved' evidence to mastery updates.

    # 1. Identify relevant LearningItems from evidence.content or evidence.activity
    # This is a major NLP/AI task or requires explicit mapping.
    # For example, search LearningItems whose content appears in evidence.content.

    # 2. For each identified LearningItem:
    #    - Retrieve or create UserProgress.
    #    - Update mastery_level significantly if evidence was approved and content seems mastered.
    #    - Record as a strong positive interaction.

    print(f"Placeholder: Updating progress from approved evidence {evidence.id}")
    # For now, no direct implementation here, just a note of placeholder status.
    pass

def get_next_learning_items_for_user(db: Session, user_id: UUID, theme_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Helper function to get next learning items using the inference service.
    This encapsulates the logic for selecting practice items.
    """
    inference_service = KnowledgeInferenceService(db)
    return inference_service.get_learning_items_for_practice(user_id, theme_id, limit)

def generate_dashboard_data(db: Session, user_id: UUID, theme_id: UUID) -> Dict[str, Any]:
    """
    Helper to generate data for the dashboard, including heatmap and levels.
    """
    inference_service = KnowledgeInferenceService(db)

    # Fetch all progress records for the user & theme
    user_progress_records = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.theme_id == theme_id
    ).all()

    # Fetch associated LearningItems and Theme details to interpret progress
    all_theme_items = db.query(LearningItem).filter(LearningItem.theme_id == theme_id).all()
    theme = db.query(Theme).filter(Theme.id == theme_id).first()

    # Map progress records to items for easier processing
    progress_map = {p.learning_item_id: p for p in user_progress_records}

    # Create a list of item data including progress for heatmap/level calc
    items_with_progress_data = []
    for item in all_theme_items:
        progress = progress_map.get(item.id)
        if progress:
            items_with_progress_data.append({"item": item, "progress": progress})

    # Generate heatmap and level data
    dashboard_metrics = inference_service.determine_level_and_heatmap(items_with_progress_data, theme.name)

    # Add aggregated theme mastery for overall score
    all_masteries = [item_data["progress"].mastery_level for item_data in items_with_progress_data if item_data["progress"]]
    overall_mastery = sum(all_masteries) / len(all_masteries) if all_masteries else 0.0

    dashboard_metrics["overall_theme_mastery_score"] = round(overall_mastery * 100, 2)
    dashboard_metrics["average_mastery"] = round(overall_mastery, 2)

    return dashboard_metrics


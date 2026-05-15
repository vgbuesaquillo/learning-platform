from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID as UUID_TYPE
import enum # Import enum for the enums defined in this schema

# Import models and Enums from models.py
# This ensures consistency between ORM models and Pydantic schemas.
from app.domain.models import (
    Theme as ThemeModel,
    LearningItem as LearningItemModel,
    UserInteraction as UserInteractionModel,
    UserProgress as UserProgressModel,
    User as UserModel,
    DomainLevel, EvidenceType, EvidenceStatus, # Enums to be directly used
    # Include other models if their schemas also need to be defined here or related
    LearningModule as LearningModuleModel,
    Competency as CompetencyModel,
    Activity as ActivityModel,
    LearningEvidence as LearningEvidenceModel,
)

# ── Schemas para Temas ───────────────────────────────────────────────────────
class ThemeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True

class ThemeCreate(ThemeBase):
    pass

class ThemeUpdate(ThemeBase):
    pass

class ThemeInDBBase(ThemeBase):
    id: UUID_TYPE
    created_at: datetime

    class Config:
        from_attributes = True # Use from_attributes=True instead of orm_mode=True

class Theme(ThemeInDBBase):
    pass # No additional fields for now

# ── Schemas para Elementos de Aprendizaje ────────────────────────────────────
class LearningItemBase(BaseModel):
    theme_id: UUID_TYPE
    item_type: str = Field(..., min_length=1, max_length=50) # e.g., "vocabulary", "phrase", "idiom"
    content: str = Field(..., min_length=1)
    item_metadata: Dict[str, Any] = Field(default_factory=dict)

class LearningItemCreate(LearningItemBase):
    pass

class LearningItemUpdate(LearningItemBase):
    pass

class LearningItemInDBBase(LearningItemBase):
    id: UUID_TYPE
    created_at: datetime

    class Config:
        from_attributes = True

class LearningItem(LearningItemInDBBase):
    pass

# ── Schemas para Interacciones del Estudiante ────────────────────────────────
class UserInteractionBase(BaseModel):
    user_id: UUID_TYPE
    learning_item_id: UUID_TYPE
    theme_id: UUID_TYPE
    interaction_type: str = Field(..., min_length=1, max_length=100) # e.g., "used_in_sentence", "identified_in_context"
    context_data: Dict[str, Any] = Field(default_factory=dict)

class UserInteractionCreate(UserInteractionBase):
    pass

class UserInteractionInDBBase(UserInteractionBase):
    id: UUID_TYPE
    timestamp: datetime

    class Config:
        from_attributes = True

class UserInteraction(UserInteractionInDBBase):
    pass

# ── Schemas para Progreso del Usuario (Adaptado) ─────────────────────────────
class UserProgressBase(BaseModel):
    user_id: UUID_TYPE
    theme_id: UUID_TYPE
    learning_item_id: UUID_TYPE

    mastery_level: float = Field(..., ge=0.0, le=1.0) # Infered mastery score (0.0 to 1.0)
    recurrence_score: int = Field(default=0, ge=0)   # Score for determining presentation frequency

class UserProgressCreate(UserProgressBase):
    pass

class UserProgressUpdate(BaseModel): # Partial update schema
    mastery_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    recurrence_score: Optional[int] = Field(None, ge=0)
    last_practiced_at: Optional[datetime] = None
    history: Optional[List[Dict[str, Any]]] = None

class UserProgressInDBBase(UserProgressBase):
    id: UUID_TYPE
    last_practiced_at: Optional[datetime] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserProgress(UserProgressInDBBase):
    pass

# ── Schemas para Usuario (adaptación de relaciones) ─────────────────────────
# Based on models.py, User model includes relationships.
# These schemas should reflect that.
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: Optional[bool] = True
    is_instructor: Optional[bool] = False

class UserCreate(UserBase):
    password: str # Password should be handled securely, not directly exposed in APIs usually

class UserUpdate(BaseModel): # Allow partial updates
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_instructor: Optional[bool] = None

class UserInDBBase(UserBase):
    id: UUID_TYPE
    hashed_password: str # Hashed password for database representation
    created_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    # Relationship to UserProgress needs to be explicitly defined or handled.
    # If User model in models.py has 'progress_records' pointing to UserProgress,
    # its schema should expose it.
    # For now, we assume `progress_records` field might be an ORM object and not directly listable Pydantic model.
    # If needed, explicitly define it here, e.g.:
    # progress_records: List[UserProgress] = []
    pass # Placeholder, actual fields might be populated by ORM

# ── Schemas para el módulo de aprendizaje y competencias (si se mantienen) ─────
class LearningModuleBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    topic: Optional[str] = None # e.g., "Research Methodology", "Python Programming"
    estimated_hours: int = 0
    is_published: bool = False

class LearningModuleCreate(LearningModuleBase):
    pass

class LearningModuleUpdate(LearningModuleBase):
    pass

class LearningModuleInDBBase(LearningModuleBase):
    id: UUID_TYPE
    created_at: datetime

    class Config:
        from_attributes = True

class LearningModule(LearningModuleInDBBase):
    pass

class CompetencyBase(BaseModel):
    module_id: UUID_TYPE
    name: str
    description: Optional[str] = None
    level_indicators: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0

class CompetencyCreate(CompetencyBase):
    pass

class CompetencyUpdate(CompetencyBase):
    pass

class CompetencyInDBBase(CompetencyBase):
    id: UUID_TYPE

    class Config:
        from_attributes = True

class Competency(CompetencyInDBBase):
    pass

# ── Schemas para Actividad y Evidencia (si se mantienen) ──────────────────────
class ActivityBase(BaseModel):
    module_id: UUID_TYPE
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    evidence_type: EvidenceType = EvidenceType.ACTIVIDAD
    rubric: Dict[str, Any] = Field(default_factory=dict)
    max_score: float = 100.0
    order_index: int = 0
    is_required: bool = True

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(ActivityBase):
    pass

class ActivityInDBBase(ActivityBase):
    id: UUID_TYPE

    class Config:
        from_attributes = True

class Activity(ActivityInDBBase):
    pass

class LearningEvidenceBase(BaseModel):
    user_id: UUID_TYPE
    activity_id: UUID_TYPE
    content: str
    reflection: Optional[str] = None
    confidence_level: Optional[int] = None # 1-5

    status: EvidenceStatus = EvidenceStatus.BORRADOR
    score: Optional[float] = None
    rubric_evaluation: Dict[str, Any] = Field(default_factory=dict)
    qualitative_feedback: Optional[str] = None # Feedback from instructor/system

class LearningEvidenceCreate(LearningEvidenceBase):
    pass

class LearningEvidenceUpdate(LearningEvidenceBase):
    pass

class LearningEvidenceInDBBase(LearningEvidenceBase):
    id: UUID_TYPE
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LearningEvidence(LearningEvidenceInDBBase):
    pass

# Schema for returning progress details. This will likely aggregate UserProgress.
class UserProgressDetail(BaseModel):
    learning_item_id: UUID_TYPE
    item_type: str
    content: str
    theme_id: UUID_TYPE
    theme_name: str
    mastery_level: float
    recurrence_score: int
    last_practiced_at: Optional[datetime] = None
    # Add more fields as needed for dashboard visualization

class UserProgressListResponse(BaseModel):
    user_progress: List[UserProgressDetail]

# Schema for API to get the next set of learning items for a user
# This would involve consulting UserProgress and selecting items to practice.
# Includes LearningItem fields for easy frontend use.
class NextLearningItemsResponse(BaseModel):
    theme_id: UUID_TYPE
    theme_name: str
    learning_items: List[LearningItem] # Or a subset of LearningItem fields

# Schema for API to record user interactions
class RecordInteractionResponse(BaseModel):
    interaction_id: UUID_TYPE
    message: str = "Interaction recorded successfully."

# Endpoint schemas will be defined in backend/app/api/

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from uuid import uuid4
import uuid
import enum

# SQLAlchemy declarative base
Base = declarative_base()

# Helper function to get current UTC time
def now_utc():
    return datetime.now(timezone.utc)

# --- Enums ---
class DomainLevel(enum.Enum):
    NOVICE = "Novice"
    INTERMEDIATE = "Intermediate"
    COMPETENT = "Competent"
    EXPERT = "Expert"

class EvidenceType(enum.Enum):
    ACTIVIDAD = "activity"
    PROYECTO = "project"
    INFORME = "report"

class EvidenceStatus(str, enum.Enum):
    BORRADOR = "draft"
    ENVIADA = "submitted"
    APROBADA = "approved"
    RECHAZADA = "rejected"
    OBSERVACIONES = "needs_revision"

class EnrollmentStatus(str, enum.Enum):
    ACTIVA = "active"
    FINALIZADA = "completed"
    ABANDONADA = "abandoned"


# ── Modelos SQLAlchemy ─────────────────────────────────────────────────────────

# ── Temas de aprendizaje ─────────────────────────────────────────────────
class Theme(Base):
    __tablename__ = "themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    order = Column(Integer, default=0)  # Para ordenar temas en listas
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    # Relaciones
    learning_items = relationship("LearningItem", back_populates="theme")

# ── Elementos de aprendizaje ───────────────────────────────────────────────
class LearningItem(Base):
    __tablename__ = "learning_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)  # e.g., "vocabulary", "phrase", "idiom", "grammar_rule"
    content = Column(Text, nullable=False)          # The actual vocabulary word, phrase, etc.
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    # Relaciones
    theme = relationship("Theme", back_populates="learning_items")
    user_progress = relationship("UserProgress", back_populates="learning_item")
    user_interactions = relationship("UserInteraction", back_populates="learning_item")

# ── Interacciones del Estudiante ─────────────────────────────────────────────
class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    learning_item_id = Column(UUID(as_uuid=True), ForeignKey("learning_items.id"), nullable=False, index=True)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False, index=True) # For quicker filtering

    interaction_type = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=now_utc)
    context_data = Column(JSON, default=dict)

    # Relaciones
    user = relationship("User", back_populates="user_interactions")
    learning_item = relationship("LearningItem", back_populates="user_interactions")
    theme = relationship("Theme") # No back_populates needed if Theme doesn't know about interactions directly

# ── Progreso del Usuario (Adaptado para el nuevo sistema) ─────────────────────
class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False, index=True)
    learning_item_id = Column(UUID(as_uuid=True), ForeignKey("learning_items.id"), nullable=False, index=True)

    # Directamente el nivel de maestría y score de recurrencia para un item
    mastery_level = Column(Float, default=0.0)      # Infered mastery score (e.g., 0.0 to 1.0)
    recurrence_score = Column(Integer, default=0)  # Score to determine how often to present this item. Higher means less frequent.

    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    # JSONB: history of interactions or mastery changes for detailed tracking
    history = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    # Relaciones
    user = relationship("User", back_populates="progress_records") # Assuming User model has progress_records
    theme = relationship("Theme") # No back_populates needed if Theme doesn't rely on this link
    learning_item = relationship("LearningItem", back_populates="user_progress")

# ── Usuario ────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False) # Store hashed password
    is_active = Column(Boolean, default=True)
    is_instructor = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    # Relaciones
    # Define the relationship to UserProgress, assuming UserProgress has a back_populates field
    progress_records = relationship("UserProgress", back_populates="user")
    user_interactions = relationship("UserInteraction", back_populates="user")
    learning_evidences = relationship("LearningEvidence", back_populates="user")
    enrollments = relationship("Enrollment", back_populates="user") # Added for Enrollment model

# ── Módulos de Aprendizaje (Legado, pero mantenido por ahora) ────────────────
class LearningModule(Base):
    __tablename__ = "learning_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    topic = Column(String(100)) # e.g., "Research Methodology", "Python Programming"
    estimated_hours = Column(Float, default=0.0)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    # Relationships (if any, e.g., to Activities)
    activities = relationship("Activity", back_populates="module")

# ── Actividades de Aprendizaje ────────────────────────────────────────────────
class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("learning_modules.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    evidence_type = Column(String(50), nullable=False, default=EvidenceType.ACTIVIDAD.value)
    rubric = Column(JSON, default=dict) # e.g., {"criteria": {"communication": {"max_score": 10, "description": "Clarity of explanation"}}}
    max_score = Column(Float, default=100.0)
    order_index = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    # Relaciones
    module = relationship("LearningModule", back_populates="activities")
    learning_evidences = relationship("LearningEvidence", back_populates="activity")
    activity_competencies = relationship("ActivityCompetency", back_populates="activity") # Link between Activity and Competency

# ── Evidencias de Aprendizaje ──────────────────────────────────────────────────
class LearningEvidence(Base):
    __tablename__ = "learning_evidences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id"), nullable=False, index=True)

    content = Column(Text, nullable=False)
    reflection = Column(Text) # Student's reflection on the work
    confidence_level = Column(Integer, nullable=True) # Student's confidence (e.g., 1-5 scale)

    status = Column(String(50), default=EvidenceStatus.BORRADOR.value, nullable=False)
    score = Column(Float, nullable=True) # Score awarded by instructor
    rubric_evaluation = Column(JSON, default=dict) # Detailed rubric scoring
    qualitative_feedback = Column(Text) # Instructor's qualitative feedback

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    # Relaciones
    user = relationship("User", back_populates="learning_evidences")
    activity = relationship("Activity", back_populates="learning_evidences")


# ── Relaciones entre Actividades/Evidencias y Competencias (Legado/Opcional) ───
class ActivityCompetency(Base): # Many-to-many between Activity and Competency
    __tablename__ = "activity_competencies"

    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id"), primary_key=True)
    competency_id = Column(UUID(as_uuid=True), ForeignKey("competencies.id"), primary_key=True)

    # Relaciones
    activity = relationship("Activity", back_populates="activity_competencies")
    competency = relationship("Competency", back_populates="activity_competencies")

class Competency(Base): # Competencies to be mapped to skills/knowledge areas
    __tablename__ = "competencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    level_indicators = Column(JSON, default=dict) # e.g., {"expert": "Can apply concepts in novel situations"}
    weight = Column(Float, default=1.0) # Weight for competency contribution to overall score
    created_at = Column(DateTime(timezone=True), default=now_utc)

    # Relaciones
    activity_competencies = relationship("ActivityCompetency", back_populates="competency")

# ── Inscripciones (Legado u otro tipo de modelo de usuario) ─────────────────────
class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("learning_modules.id"), nullable=False, index=True)
    status = Column(String(50), default=EnrollmentStatus.ACTIVA.value, nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=now_utc)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    user = relationship("User", back_populates="enrollments")
    module = relationship("LearningModule")
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
    # Users might have a preferred theme or be enrolled in multiple,
    # this could be a many-to-many or a preferred_theme_id on User
    # For now, let's assume UserProgress links to a theme_id

# ── Elementos de aprendizaje ───────────────────────────────────────────────
class LearningItem(Base):
    __tablename__ = "learning_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)  # e.g., "vocabulary", "phrase", "idiom", "grammar_rule"
    content = Column(Text, nullable=False)          # The actual vocabulary word, phrase, etc.
    # JSONB for contextual metadata, associations, example sentences, etc.
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

    # Type of interaction that helps infer knowledge
    # e.g., "used_in_sentence", "identified_in_context", "written_correctly", "spoken_correctly", "identified_in_audio"
    interaction_type = Column(String(100), nullable=False)

    # Timestamp of the interaction
    timestamp = Column(DateTime(timezone=True), default=now_utc)

    # Additional data related to the interaction, e.g., the sentence where the item was used
    context_data = Column(JSON, default=dict)

    # Relaciones
    user = relationship("User", back_populates="user_interactions")
    learning_item = relationship("LearningItem", back_populates="user_interactions")
    theme = relationship("Theme") # No back_populates needed if Theme doesn't know about interactions directly


# ── Progreso del Usuario (Adaptado para el nuevo sistema) ─────────────────────
# Redefinimos CompetencyProgress to be UserProgress for this new model
# We will link UserProgress to LearningItem and Theme, not directly to Competency.
# The "mastery_level" and "recurrence_score" are the new key fields.
class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False, index=True)
    learning_item_id = Column(UUID(as_uuid=True), ForeignKey("learning_items.id"), nullable=False, index=True)

    # New fields for adaptive learning
    mastery_level = Column(Float, default=0.0)      # Infered mastery score (e.g., 0.0 to 1.0)
    recurrence_score = Column(Integer, default=0)  # Score to determine how often to present this item. Higher means less frequent.

    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    # JSONB: history of interactions or mastery changes for detailed tracking
    history = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    # Relaciones
    user = relationship("User", back_populates="progress_records") # Assuming User model has progress_records = relationship("UserProgress", back_populates="user")
    theme = relationship("Theme") # No bac_populates needed if Theme doesn't rely on this link
    learning_item = relationship("LearningItem", back_populates="user_progress")

# Nota: Este cambio introduce nuevos modelos. A continuación, se deben actualizar referencias en User y otros modelos.
"""Esquema inicial LearnPath

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    domain_level = postgresql.ENUM(
        "novato", "intermedio", "competente", "experto",
        name="domainlevel"
    )
    evidence_type = postgresql.ENUM(
        "actividad", "proyecto", "autoevaluacion", "reflexion", "portfolio",
        name="evidencetype"
    )
    evidence_status = postgresql.ENUM(
        "borrador", "enviada", "revisada", "aprobada",
        name="evidencestatus"
    )
    domain_level.create(op.get_bind())
    evidence_type.create(op.get_bind())
    evidence_status.create(op.get_bind())

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("is_instructor", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # learning_modules
    op.create_table(
        "learning_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("topic", sa.String(255)),
        sa.Column("estimated_hours", sa.Integer, server_default="0"),
        sa.Column("is_published", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # competencies
    op.create_table(
        "competencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("learning_modules.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("level_indicators", postgresql.JSONB, server_default="{}"),
        sa.Column("weight", sa.Float, server_default="1.0"),
    )

    # activities
    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("learning_modules.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("instructions", sa.Text),
        sa.Column("evidence_type", sa.Enum(name="evidencetype"), nullable=False),
        sa.Column("rubric", postgresql.JSONB, server_default="{}"),
        sa.Column("max_score", sa.Float, server_default="100.0"),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("is_required", sa.Boolean, server_default="true"),
    )

    # activity_competencies (M:N)
    op.create_table(
        "activity_competencies",
        sa.Column("activity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("activities.id"), primary_key=True),
        sa.Column("competency_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("competencies.id"), primary_key=True),
        sa.Column("contribution_weight", sa.Float, server_default="1.0"),
    )

    # enrollments
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("learning_modules.id"), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # learning_evidences
    op.create_table(
        "learning_evidences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("reflection", sa.Text),
        sa.Column("confidence_level", sa.Integer),
        sa.Column("status", sa.Enum(name="evidencestatus"), server_default="borrador"),
        sa.Column("score", sa.Float),
        sa.Column("rubric_evaluation", postgresql.JSONB, server_default="{}"),
        sa.Column("qualitative_feedback", sa.Text),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_evidences_user", "learning_evidences", ["user_id"])
    op.create_index("ix_evidences_activity", "learning_evidences", ["activity_id"])

    # competency_progress
    op.create_table(
        "competency_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("competency_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("competencies.id"), nullable=False),
        sa.Column("current_level", sa.Enum(name="domainlevel"), server_default="novato"),
        sa.Column("domain_score", sa.Float, server_default="0.0"),
        sa.Column("consistency_score", sa.Float, server_default="0.0"),
        sa.Column("evidence_count", sa.Integer, server_default="0"),
        sa.Column("last_evidence_at", sa.DateTime(timezone=True)),
        sa.Column("history", postgresql.JSONB, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_progress_user_comp", "competency_progress",
                    ["user_id", "competency_id"], unique=True)


def downgrade() -> None:
    op.drop_table("competency_progress")
    op.drop_table("learning_evidences")
    op.drop_table("enrollments")
    op.drop_table("activity_competencies")
    op.drop_table("activities")
    op.drop_table("competencies")
    op.drop_table("learning_modules")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS domainlevel")
    op.execute("DROP TYPE IF EXISTS evidencetype")
    op.execute("DROP TYPE IF EXISTS evidencestatus")

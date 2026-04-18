"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("gps_lat", sa.Numeric(10, 7)),
        sa.Column("gps_lng", sa.Numeric(10, 7)),
        sa.Column("normalized_address", sa.Text()),
        sa.Column("location_source", sa.String(length=32)),
        sa.Column("optional_inputs", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "image_metadata",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("file_size_bytes", sa.Integer()),
        sa.Column("quality_score", sa.Float()),
        sa.Column("blur_score", sa.Float()),
        sa.Column("brightness_score", sa.Float()),
        sa.Column("phash", sa.String(length=64)),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "extracted_features",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("visual_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("geo_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("qc_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("feature_vector", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("out_of_distribution_score", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_snapshot_id", sa.String(length=36), sa.ForeignKey("extracted_features.id")),
        sa.Column("underwriting_model_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("daily_sales_min", sa.Numeric(14, 2)),
        sa.Column("daily_sales_max", sa.Numeric(14, 2)),
        sa.Column("monthly_revenue_min", sa.Numeric(14, 2)),
        sa.Column("monthly_revenue_max", sa.Numeric(14, 2)),
        sa.Column("monthly_income_min", sa.Numeric(14, 2)),
        sa.Column("monthly_income_max", sa.Numeric(14, 2)),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("recommendation", sa.String(length=64)),
        sa.Column("eligibility", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("benchmark", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("explanation_merchant", sa.Text()),
        sa.Column("explanation_underwriter", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "risk_flags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("prediction_id", sa.String(length=36), sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("flag_code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("sessions.id")),
        sa.Column("prediction_id", sa.String(length=36), sa.ForeignKey("predictions.id")),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=36)),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "job_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("sessions.id")),
        sa.Column("prediction_id", sa.String(length=36), sa.ForeignKey("predictions.id")),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_sessions_user_created", "sessions", ["user_id", "created_at"])
    op.create_index("idx_image_metadata_session_role", "image_metadata", ["session_id", "role"])
    op.create_index("idx_predictions_session_created", "predictions", ["session_id", "created_at"])
    op.create_index("idx_predictions_status_created", "predictions", ["status", "created_at"])
    op.create_index("idx_risk_flags_prediction_severity", "risk_flags", ["prediction_id", "severity"])
    op.create_index("idx_audit_logs_session_created", "audit_logs", ["session_id", "created_at"])
    op.create_index("idx_audit_logs_prediction_created", "audit_logs", ["prediction_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_logs_prediction_created", table_name="audit_logs")
    op.drop_index("idx_audit_logs_session_created", table_name="audit_logs")
    op.drop_index("idx_risk_flags_prediction_severity", table_name="risk_flags")
    op.drop_index("idx_predictions_status_created", table_name="predictions")
    op.drop_index("idx_predictions_session_created", table_name="predictions")
    op.drop_index("idx_image_metadata_session_role", table_name="image_metadata")
    op.drop_index("idx_sessions_user_created", table_name="sessions")
    op.drop_table("job_runs")
    op.drop_table("audit_logs")
    op.drop_table("risk_flags")
    op.drop_table("predictions")
    op.drop_table("extracted_features")
    op.drop_table("image_metadata")
    op.drop_table("sessions")
    op.drop_table("users")


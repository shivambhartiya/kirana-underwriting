from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.enums import PredictionStatus
from app.utils.ids import new_id


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    feature_snapshot_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("extracted_features.id"))
    underwriting_model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PredictionStatus.queued.value, nullable=False)
    daily_sales_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    daily_sales_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    monthly_revenue_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    monthly_revenue_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    monthly_income_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    monthly_income_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    recommendation: Mapped[str | None] = mapped_column(String(64))
    eligibility: Mapped[dict | None] = mapped_column(JSON)
    benchmark: Mapped[dict | None] = mapped_column(JSON)
    explanation_merchant: Mapped[str | None] = mapped_column(Text)
    explanation_underwriter: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

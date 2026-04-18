from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.ids import new_id


class ExtractedFeatures(Base):
    __tablename__ = "extracted_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    visual_features: Mapped[dict] = mapped_column(JSON, nullable=False)
    geo_features: Mapped[dict] = mapped_column(JSON, nullable=False)
    qc_features: Mapped[dict] = mapped_column(JSON, nullable=False)
    feature_vector: Mapped[dict] = mapped_column(JSON, nullable=False)
    out_of_distribution_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

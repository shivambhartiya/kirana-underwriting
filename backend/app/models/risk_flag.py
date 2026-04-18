from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.ids import new_id


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    prediction_id: Mapped[str] = mapped_column(String(36), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    flag_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

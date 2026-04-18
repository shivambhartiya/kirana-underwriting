from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.ids import new_id


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sessions.id"))
    prediction_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("predictions.id"))
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

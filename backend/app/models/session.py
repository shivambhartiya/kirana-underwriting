from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.enums import SessionStatus
from app.utils.ids import new_id


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=SessionStatus.draft.value, nullable=False)
    gps_lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    gps_lng: Mapped[float | None] = mapped_column(Numeric(10, 7))
    normalized_address: Mapped[str | None] = mapped_column(Text)
    location_source: Mapped[str | None] = mapped_column(String(32))
    optional_inputs: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

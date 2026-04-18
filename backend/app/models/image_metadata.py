from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.ids import new_id


class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    object_key: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    quality_score: Mapped[float | None] = mapped_column(Float)
    blur_score: Mapped[float | None] = mapped_column(Float)
    brightness_score: Mapped[float | None] = mapped_column(Float)
    phash: Mapped[str | None] = mapped_column(String(64))
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


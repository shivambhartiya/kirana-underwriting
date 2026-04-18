from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.image_metadata import ImageMetadata
from app.models.session import SessionRecord


class SessionRepo:
    def __init__(self, db: Session):
        self.db = db

    def get(self, session_id: str) -> SessionRecord | None:
        return self.db.get(SessionRecord, session_id)

    def create(self, session: SessionRecord) -> SessionRecord:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def save(self, session: SessionRecord) -> SessionRecord:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_images(self, session_id: str) -> list[ImageMetadata]:
        return list(self.db.scalars(select(ImageMetadata).where(ImageMetadata.session_id == session_id)))


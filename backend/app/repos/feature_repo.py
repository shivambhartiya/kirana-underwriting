from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extracted_features import ExtractedFeatures


class FeatureRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, features: ExtractedFeatures) -> ExtractedFeatures:
        self.db.add(features)
        self.db.commit()
        self.db.refresh(features)
        return features

    def get_latest_for_session(self, session_id: str) -> ExtractedFeatures | None:
        stmt = (
            select(ExtractedFeatures)
            .where(ExtractedFeatures.session_id == session_id)
            .order_by(ExtractedFeatures.created_at.desc())
        )
        return self.db.scalar(stmt)


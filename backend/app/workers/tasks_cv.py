from app.core.database import SessionLocal
from app.repos.feature_repo import FeatureRepo
from app.repos.session_repo import SessionRepo
from app.services.image_feature_service import ImageFeatureService


def extract_visual_features(session_id: str) -> tuple[dict, dict]:
    db = SessionLocal()
    try:
        images = SessionRepo(db).list_images(session_id)
        return ImageFeatureService().extract_features(images)
    finally:
        db.close()


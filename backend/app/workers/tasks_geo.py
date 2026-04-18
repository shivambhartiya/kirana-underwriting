from app.core.database import SessionLocal
from app.repos.session_repo import SessionRepo
from app.services.geo_service import GeoService


def enrich_geo_features(session_id: str) -> dict:
    db = SessionLocal()
    try:
        session = SessionRepo(db).get(session_id)
        if not session or session.gps_lat is None or session.gps_lng is None:
            return {}
        _, _, _, geo_features = GeoService().normalize_location(float(session.gps_lat), float(session.gps_lng), session.location_source or "stored")
        return geo_features
    finally:
        db.close()


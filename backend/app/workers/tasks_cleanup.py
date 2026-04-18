from datetime import datetime, timedelta

from app.core.config import get_settings


def raw_image_expiry_deadline() -> datetime:
    settings = get_settings()
    return datetime.utcnow() - timedelta(hours=settings.raw_image_retention_hours)


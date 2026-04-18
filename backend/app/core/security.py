from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings


settings = get_settings()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(subject: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.refresh_token_expire_minutes)
    payload = {"sub": subject, "exp": expires_at, "type": "refresh"}
    return jwt.encode(payload, settings.jwt_refresh_secret, algorithm="HS256")

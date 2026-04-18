from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.repos.user_repo import UserRepo
from app.utils.enums import Role


settings = get_settings()


DbSession = Annotated[Session, Depends(get_db)]


def _get_or_create_demo_user(db: Session):
    repo = UserRepo(db)
    demo_email = "demo@kirana.local"
    user = repo.get_by_email(demo_email)
    if user:
        return user
    demo_user = User(
        email=demo_email,
        password_hash=hash_password("password123"),
        full_name="Demo Merchant",
        role=Role.merchant.value,
    )
    return repo.create(demo_user)


def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
):
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            try:
                payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
                subject = payload.get("sub")
                if not subject:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
                user = UserRepo(db).get_by_id(str(subject))
                if not user:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
                return user
            except JWTError as error:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from error

    if settings.app_env == "local":
        return _get_or_create_demo_user(db)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

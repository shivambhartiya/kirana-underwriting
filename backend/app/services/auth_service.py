from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User
from app.repos.user_repo import UserRepo
from app.schemas.auth import LoginRequest, TokenResponse, UserCreateRequest, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepo(db)

    def register(self, payload: UserCreateRequest) -> UserResponse:
        if self.repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role.value,
        )
        return UserResponse.model_validate(self.repo.create(user))

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            user=UserResponse.model_validate(user),
        )


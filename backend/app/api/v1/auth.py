from fastapi import APIRouter, Depends

from app.api.v1.deps import DbSession, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserCreateRequest, UserResponse
from app.services.auth_service import AuthService


router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(payload: UserCreateRequest, db: DbSession):
    return AuthService(db).register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession):
    return AuthService(db).login(payload)


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse.model_validate(user)


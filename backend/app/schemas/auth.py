from pydantic import BaseModel, EmailStr

from app.utils.enums import Role


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: Role = Role.merchant


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    role: Role

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


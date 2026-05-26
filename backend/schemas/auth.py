from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool = True

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "agent"


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    password: str | None = None

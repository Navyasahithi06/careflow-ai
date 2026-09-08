from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True

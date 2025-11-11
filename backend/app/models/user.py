from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RoleResponse(BaseModel):
    id: str
    name: str
    permissions: dict

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    name: Optional[str] = None
    picture: Optional[str] = None
    is_active: bool
    is_verified: bool
    default_tenant_id: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class EmailVerification(BaseModel):
    token: str


# Legacy support for old OAuth flow
class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    google_id: Optional[str] = None

    class Config:
        from_attributes = True

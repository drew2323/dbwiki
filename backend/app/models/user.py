from pydantic import BaseModel, EmailStr
from typing import Optional


class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    google_id: str

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with additional fields for database storage"""
    created_at: str
    last_login: str

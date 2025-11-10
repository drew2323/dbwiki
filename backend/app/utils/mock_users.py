from typing import Dict, Optional
from app.models.user import UserInDB
from datetime import datetime
import uuid


# Mock user storage (in-memory)
mock_users: Dict[str, UserInDB] = {}


def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email"""
    return next((user for user in mock_users.values() if user.email == email), None)


def get_user_by_google_id(google_id: str) -> Optional[UserInDB]:
    """Get user by Google ID"""
    return next((user for user in mock_users.values() if user.google_id == google_id), None)


def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Get user by ID"""
    return mock_users.get(user_id)


def create_user(email: str, name: str, google_id: str, picture: Optional[str] = None) -> UserInDB:
    """Create a new user"""
    user_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    user = UserInDB(
        id=user_id,
        email=email,
        name=name,
        picture=picture,
        google_id=google_id,
        created_at=now,
        last_login=now
    )

    mock_users[user_id] = user
    return user


def update_last_login(user_id: str) -> Optional[UserInDB]:
    """Update user's last login timestamp"""
    user = mock_users.get(user_id)
    if user:
        user.last_login = datetime.now().isoformat()
    return user

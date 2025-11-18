from sqlalchemy.orm import Session
from app.models.db_models import User, Role, Space, UserSpaceRole, AuthIdentity
from typing import Optional
from datetime import datetime, timezone
import uuid

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_provider_identity(db: Session, provider: str, provider_subject: str) -> Optional[User]:
    """Get user by their auth identity (e.g., google_id, email for password)"""
    identity = db.query(AuthIdentity).filter(
        AuthIdentity.provider == provider,
        AuthIdentity.provider_subject == provider_subject
    ).first()
    return identity.user if identity else None

def create_user(
    db: Session,
    email: str,
    username: str,
    name: Optional[str] = None,
    picture: Optional[str] = None,
    is_verified: bool = False
) -> User:
    """
    Create a new user.
    Note: Space membership should be added separately using user_space_roles CRUD.
    Note: Auth identities should be created separately using auth_identities CRUD.
    """
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=email,
        username=username,
        name=name,
        picture=picture,
        is_verified=is_verified,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_last_login(db: Session, user_id: str) -> None:
    db.query(User).filter(User.id == user_id).update({"last_login": datetime.now(timezone.utc)})
    db.commit()

def update_user_verification_token(db: Session, user_id: str, token: str) -> None:
    db.query(User).filter(User.id == user_id).update({"verification_token": token})
    db.commit()

def verify_user(db: Session, token: str) -> Optional[User]:
    user = db.query(User).filter(User.verification_token == token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.commit()
        db.refresh(user)
    return user

def update_reset_token(db: Session, user_id: str, token: str, expires: datetime) -> None:
    db.query(User).filter(User.id == user_id).update({
        "reset_token": token,
        "reset_token_expires": expires
    })
    db.commit()

def reset_password(db: Session, token: str, new_password_hash: str) -> Optional[User]:
    """Reset password for a user. Updates the password identity's metadata."""
    user = db.query(User).filter(
        User.reset_token == token,
        User.reset_token_expires > datetime.now(timezone.utc)
    ).first()
    if user:
        # Update the password identity
        password_identity = db.query(AuthIdentity).filter(
            AuthIdentity.user_id == user.id,
            AuthIdentity.provider == 'password'
        ).first()
        if password_identity:
            password_identity.provider_metadata = {"password_hash": new_password_hash}
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        db.refresh(user)
    return user

def get_users(db: Session, space_id: Optional[str] = None, skip: int = 0, limit: int = 100):
    """
    Get all users, optionally filtered by space membership.

    Args:
        db: Database session
        space_id: Optional space ID to filter users by space membership
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
    """
    query = db.query(User)

    # Filter by space membership if space_id provided
    if space_id:
        query = query.join(UserSpaceRole).filter(UserSpaceRole.space_id == space_id)

    return query.offset(skip).limit(limit).all()

def deactivate_user(db: Session, user_id: str) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user

def activate_user(db: Session, user_id: str) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = True
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: str) -> bool:
    """
    Permanently delete a user and all associated data via CASCADE.

    This will automatically delete (via database CASCADE):
    - All auth_identities (passwords, OAuth connections)
    - All user_space_roles (space memberships)

    Returns:
        bool: True if user was found and deleted, False if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

"""
CRUD operations for multi-space user access management.
"""
from sqlalchemy.orm import Session
from app.models.db_models import User, Role, Space, UserSpaceRole
from typing import Optional, List
from datetime import datetime, timezone
import uuid

def get_user_spaces(db: Session, user_id: str) -> List[Space]:
    """Get all spaces a user has access to"""
    return db.query(Space)\
        .join(UserSpaceRole)\
        .filter(UserSpaceRole.user_id == user_id)\
        .filter(UserSpaceRole.is_active == True)\
        .all()

def get_user_role_in_space(db: Session, user_id: str, space_id: str) -> Optional[Role]:
    """Get user's role in a specific space"""
    usr = db.query(UserSpaceRole)\
        .filter(UserSpaceRole.user_id == user_id)\
        .filter(UserSpaceRole.space_id == space_id)\
        .filter(UserSpaceRole.is_active == True)\
        .first()

    if usr:
        return usr.role
    return None

def get_user_space_role(db: Session, user_id: str, space_id: str) -> Optional[UserSpaceRole]:
    """Get UserSpaceRole association"""
    return db.query(UserSpaceRole)\
        .filter(UserSpaceRole.user_id == user_id)\
        .filter(UserSpaceRole.space_id == space_id)\
        .first()

def add_user_to_space(
    db: Session,
    user_id: str,
    space_id: str,
    role_id: str,
    expires_at: Optional[datetime] = None
) -> UserSpaceRole:
    """Add user to a space with specified role"""
    # Check if association already exists
    existing = get_user_space_role(db, user_id, space_id)
    if existing:
        # Update existing
        existing.role_id = role_id
        existing.is_active = True
        existing.expires_at = expires_at
        db.commit()
        db.refresh(existing)
        return existing

    # Create new association
    usr = UserSpaceRole(
        id=str(uuid.uuid4()),
        user_id=user_id,
        space_id=space_id,
        role_id=role_id,
        is_active=True,
        expires_at=expires_at
    )
    db.add(usr)
    db.commit()
    db.refresh(usr)
    return usr

def remove_user_from_space(db: Session, user_id: str, space_id: str) -> bool:
    """Remove user's access to a space"""
    usr = get_user_space_role(db, user_id, space_id)
    if usr:
        db.delete(usr)
        db.commit()
        return True
    return False

def deactivate_user_in_space(db: Session, user_id: str, space_id: str) -> bool:
    """Deactivate user's access without deleting the record"""
    usr = get_user_space_role(db, user_id, space_id)
    if usr:
        usr.is_active = False
        db.commit()
        return True
    return False

def update_user_role_in_space(
    db: Session,
    user_id: str,
    space_id: str,
    new_role_id: str
) -> Optional[UserSpaceRole]:
    """Update user's role in a specific space"""
    usr = get_user_space_role(db, user_id, space_id)
    if usr:
        usr.role_id = new_role_id
        db.commit()
        db.refresh(usr)
        return usr
    return None

def get_space_users(db: Session, space_id: str, include_inactive: bool = False) -> List[User]:
    """Get all users who have access to a space"""
    query = db.query(User)\
        .join(UserSpaceRole)\
        .filter(UserSpaceRole.space_id == space_id)

    if not include_inactive:
        query = query.filter(UserSpaceRole.is_active == True)

    return query.all()

def user_has_access_to_space(db: Session, user_id: str, space_id: str) -> bool:
    """
    Check if user has active access to a space.
    Superusers automatically have access to all spaces.
    """
    from app.crud import users as user_crud

    # Check if user is superuser
    user = user_crud.get_user_by_id(db, user_id)
    if user and user.is_superuser:
        return True

    # Check for explicit space membership
    usr = db.query(UserSpaceRole)\
        .filter(UserSpaceRole.user_id == user_id)\
        .filter(UserSpaceRole.space_id == space_id)\
        .filter(UserSpaceRole.is_active == True)\
        .first()
    return usr is not None

def get_user_permissions_in_space(db: Session, user_id: str, space_id: str) -> dict:
    """
    Get user's effective permissions in a space.
    Superusers get all permissions.
    """
    from app.crud import users as user_crud

    # Superusers have all permissions
    user = user_crud.get_user_by_id(db, user_id)
    if user and user.is_superuser:
        return {"all": True}  # Superusers have all permissions

    role = get_user_role_in_space(db, user_id, space_id)
    if role:
        return role.permissions
    return {}

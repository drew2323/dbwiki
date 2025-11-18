"""
CRUD operations for global roles.
Roles are now global entities (superuser, admin, edit, read) that can be assigned to users in different spaces.
"""
from sqlalchemy.orm import Session
from app.models.db_models import Role
from typing import Optional, List
import uuid

def get_role_by_id(db: Session, role_id: str) -> Optional[Role]:
    """Get role by ID"""
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """Get role by name (globally unique)"""
    return db.query(Role).filter(Role.name == name).first()

def get_all_roles(db: Session) -> List[Role]:
    """Get all global roles"""
    return db.query(Role).all()

def create_role(
    db: Session,
    name: str,
    permissions: dict
) -> Role:
    """Create a new global role"""
    role = Role(
        id=str(uuid.uuid4()),
        name=name,
        permissions=permissions
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def update_role(db: Session, role_id: str, name: Optional[str] = None, permissions: Optional[dict] = None) -> Optional[Role]:
    """Update role name and/or permissions"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if role:
        if name is not None:
            role.name = name
        if permissions is not None:
            role.permissions = permissions
        db.commit()
        db.refresh(role)
    return role

def update_role_permissions(db: Session, role_id: str, permissions: dict) -> Optional[Role]:
    """Update role permissions (legacy function, kept for compatibility)"""
    return update_role(db, role_id, permissions=permissions)

def delete_role(db: Session, role_id: str) -> bool:
    """Delete a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if role:
        db.delete(role)
        db.commit()
        return True
    return False

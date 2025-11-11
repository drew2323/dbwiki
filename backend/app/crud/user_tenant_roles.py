"""
CRUD operations for multi-tenant user access management.
"""
from sqlalchemy.orm import Session
from app.models.db_models import User, Role, Tenant, UserTenantRole
from typing import Optional, List
from datetime import datetime, timezone
import uuid

def get_user_tenants(db: Session, user_id: str) -> List[Tenant]:
    """Get all tenants a user has access to"""
    return db.query(Tenant)\
        .join(UserTenantRole)\
        .filter(UserTenantRole.user_id == user_id)\
        .filter(UserTenantRole.is_active == True)\
        .all()

def get_user_role_in_tenant(db: Session, user_id: str, tenant_id: str) -> Optional[Role]:
    """Get user's role in a specific tenant"""
    utr = db.query(UserTenantRole)\
        .filter(UserTenantRole.user_id == user_id)\
        .filter(UserTenantRole.tenant_id == tenant_id)\
        .filter(UserTenantRole.is_active == True)\
        .first()

    if utr:
        return utr.role
    return None

def get_user_tenant_role(db: Session, user_id: str, tenant_id: str) -> Optional[UserTenantRole]:
    """Get UserTenantRole association"""
    return db.query(UserTenantRole)\
        .filter(UserTenantRole.user_id == user_id)\
        .filter(UserTenantRole.tenant_id == tenant_id)\
        .first()

def add_user_to_tenant(
    db: Session,
    user_id: str,
    tenant_id: str,
    role_id: str,
    expires_at: Optional[datetime] = None
) -> UserTenantRole:
    """Add user to a tenant with specified role"""
    # Check if association already exists
    existing = get_user_tenant_role(db, user_id, tenant_id)
    if existing:
        # Update existing
        existing.role_id = role_id
        existing.is_active = True
        existing.expires_at = expires_at
        db.commit()
        db.refresh(existing)
        return existing

    # Create new association
    utr = UserTenantRole(
        id=str(uuid.uuid4()),
        user_id=user_id,
        tenant_id=tenant_id,
        role_id=role_id,
        is_active=True,
        expires_at=expires_at
    )
    db.add(utr)
    db.commit()
    db.refresh(utr)
    return utr

def remove_user_from_tenant(db: Session, user_id: str, tenant_id: str) -> bool:
    """Remove user's access to a tenant"""
    utr = get_user_tenant_role(db, user_id, tenant_id)
    if utr:
        db.delete(utr)
        db.commit()
        return True
    return False

def deactivate_user_in_tenant(db: Session, user_id: str, tenant_id: str) -> bool:
    """Deactivate user's access without deleting the record"""
    utr = get_user_tenant_role(db, user_id, tenant_id)
    if utr:
        utr.is_active = False
        db.commit()
        return True
    return False

def update_user_role_in_tenant(
    db: Session,
    user_id: str,
    tenant_id: str,
    new_role_id: str
) -> Optional[UserTenantRole]:
    """Update user's role in a specific tenant"""
    utr = get_user_tenant_role(db, user_id, tenant_id)
    if utr:
        utr.role_id = new_role_id
        db.commit()
        db.refresh(utr)
        return utr
    return None

def get_tenant_users(db: Session, tenant_id: str, include_inactive: bool = False) -> List[User]:
    """Get all users who have access to a tenant"""
    query = db.query(User)\
        .join(UserTenantRole)\
        .filter(UserTenantRole.tenant_id == tenant_id)

    if not include_inactive:
        query = query.filter(UserTenantRole.is_active == True)

    return query.all()

def user_has_access_to_tenant(db: Session, user_id: str, tenant_id: str) -> bool:
    """Check if user has active access to a tenant"""
    utr = db.query(UserTenantRole)\
        .filter(UserTenantRole.user_id == user_id)\
        .filter(UserTenantRole.tenant_id == tenant_id)\
        .filter(UserTenantRole.is_active == True)\
        .first()
    return utr is not None

def get_user_permissions_in_tenant(db: Session, user_id: str, tenant_id: str) -> dict:
    """Get user's effective permissions in a tenant"""
    role = get_user_role_in_tenant(db, user_id, tenant_id)
    if role:
        return role.permissions
    return {}

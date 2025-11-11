from sqlalchemy.orm import Session
from app.models.db_models import Role
from typing import Optional, List
import uuid

def get_role_by_id(db: Session, role_id: str) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, name: str, tenant_id: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name, Role.tenant_id == tenant_id).first()

def get_roles_by_tenant(db: Session, tenant_id: str) -> List[Role]:
    return db.query(Role).filter(Role.tenant_id == tenant_id).all()

def create_role(
    db: Session,
    name: str,
    permissions: dict,
    tenant_id: str
) -> Role:
    role = Role(
        id=str(uuid.uuid4()),
        name=name,
        permissions=permissions,
        tenant_id=tenant_id
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def update_role_permissions(db: Session, role_id: str, permissions: dict) -> Optional[Role]:
    role = db.query(Role).filter(Role.id == role_id).first()
    if role:
        role.permissions = permissions
        db.commit()
        db.refresh(role)
    return role

def delete_role(db: Session, role_id: str) -> bool:
    role = db.query(Role).filter(Role.id == role_id).first()
    if role:
        db.delete(role)
        db.commit()
        return True
    return False

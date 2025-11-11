from sqlalchemy.orm import Session
from app.models.db_models import Tenant
from typing import Optional, List
import uuid

def get_tenant_by_id(db: Session, tenant_id: str) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()

def get_tenant_by_subdomain(db: Session, subdomain: str) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.subdomain == subdomain).first()

def get_default_tenant(db: Session) -> Optional[Tenant]:
    """Get the default tenant (for single-tenant mode)"""
    return db.query(Tenant).filter(Tenant.name == "Default").first()

def get_all_tenants(db: Session, skip: int = 0, limit: int = 100) -> List[Tenant]:
    return db.query(Tenant).offset(skip).limit(limit).all()

def create_tenant(
    db: Session,
    name: str,
    subdomain: Optional[str] = None
) -> Tenant:
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        subdomain=subdomain,
        is_active=True
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

def update_tenant(db: Session, tenant_id: str, name: Optional[str] = None, subdomain: Optional[str] = None) -> Optional[Tenant]:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        if name:
            tenant.name = name
        if subdomain is not None:
            tenant.subdomain = subdomain
        db.commit()
        db.refresh(tenant)
    return tenant

def deactivate_tenant(db: Session, tenant_id: str) -> Optional[Tenant]:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        tenant.is_active = False
        db.commit()
        db.refresh(tenant)
    return tenant

def activate_tenant(db: Session, tenant_id: str) -> Optional[Tenant]:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant:
        tenant.is_active = True
        db.commit()
        db.refresh(tenant)
    return tenant

"""
Roles management router for CRUD operations on roles.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.crud import roles as role_crud
from app.crud import tenants as tenant_crud

router = APIRouter(prefix="/api/roles", tags=["roles"])


class RoleResponse(BaseModel):
    id: str
    name: str
    tenant_id: str
    permissions: Dict[str, Any]
    created_at: str

    class Config:
        from_attributes = True


class CreateRole(BaseModel):
    name: str
    tenant_id: str
    permissions: Dict[str, Any] = {}


class UpdateRole(BaseModel):
    name: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all roles, optionally filtered by tenant.
    If no tenant_id provided, returns roles from all tenants.
    """
    from app.models.db_models import Role

    query = db.query(Role)
    if tenant_id:
        query = query.filter(Role.tenant_id == tenant_id)

    roles = query.all()

    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            tenant_id=role.tenant_id,
            permissions=role.permissions,
            created_at=role.created_at.isoformat()
        )
        for role in roles
    ]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: str, db: Session = Depends(get_db)):
    """Get a single role by ID"""
    role = role_crud.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=role.id,
        name=role.name,
        tenant_id=role.tenant_id,
        permissions=role.permissions,
        created_at=role.created_at.isoformat()
    )


@router.post("", response_model=RoleResponse)
async def create_role(role_data: CreateRole, db: Session = Depends(get_db)):
    """Create a new role"""
    # Verify tenant exists
    tenant = tenant_crud.get_tenant_by_id(db, role_data.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check if role with same name exists in this tenant
    existing = role_crud.get_role_by_name(db, role_data.name, role_data.tenant_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Role '{role_data.name}' already exists in this tenant"
        )

    role = role_crud.create_role(
        db=db,
        name=role_data.name,
        tenant_id=role_data.tenant_id,
        permissions=role_data.permissions
    )

    return RoleResponse(
        id=role.id,
        name=role.name,
        tenant_id=role.tenant_id,
        permissions=role.permissions,
        created_at=role.created_at.isoformat()
    )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: UpdateRole,
    db: Session = Depends(get_db)
):
    """Update a role"""
    from app.models.db_models import Role

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if new name conflicts with existing role in same tenant
    if role_data.name and role_data.name != role.name:
        existing = role_crud.get_role_by_name(db, role_data.name, role.tenant_id)
        if existing and existing.id != role_id:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{role_data.name}' already exists in this tenant"
            )

    # Update fields
    if role_data.name:
        role.name = role_data.name
    if role_data.permissions is not None:
        role.permissions = role_data.permissions

    db.commit()
    db.refresh(role)

    return RoleResponse(
        id=role.id,
        name=role.name,
        tenant_id=role.tenant_id,
        permissions=role.permissions,
        created_at=role.created_at.isoformat()
    )


@router.delete("/{role_id}")
async def delete_role(role_id: str, db: Session = Depends(get_db)):
    """
    Delete a role.
    Note: This will fail if there are users currently assigned to this role.
    """
    from app.models.db_models import Role, UserTenantRole

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if any users have this role
    users_with_role = db.query(UserTenantRole).filter(
        UserTenantRole.role_id == role_id
    ).count()

    if users_with_role > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role. {users_with_role} user(s) are currently assigned to this role. Please reassign them first."
        )

    db.delete(role)
    db.commit()

    return {"message": "Role deleted successfully"}

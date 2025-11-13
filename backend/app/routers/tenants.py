"""
Tenant management API endpoints for multi-tenant support.
Allows users to manage their tenant access and switch between tenants.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.crud import user_tenant_roles as utr_crud
from app.crud import tenants as tenant_crud
from app.models.db_models import User, Tenant, Role

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


# Pydantic models for request/response
class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    subdomain: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    permissions: dict


class UserTenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant: TenantResponse
    role: RoleResponse
    is_active: bool
    created_at: datetime
    expires_at: datetime | None


class AddUserToTenantRequest(BaseModel):
    tenant_id: str
    role_id: str
    expires_at: datetime | None = None


class UpdateRoleRequest(BaseModel):
    role_id: str


# Endpoints
@router.get("/me", response_model=List[UserTenantResponse])
async def get_my_tenants(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all tenants the current user has access to with their roles.
    """
    tenants = utr_crud.get_user_tenants(db, user.id)

    result = []
    for tenant in tenants:
        role = utr_crud.get_user_role_in_tenant(db, user.id, tenant.id)
        utr = utr_crud.get_user_tenant_role(db, user.id, tenant.id)

        if role and utr:
            result.append({
                "tenant": tenant,
                "role": role,
                "is_active": utr.is_active,
                "created_at": utr.created_at,
                "expires_at": utr.expires_at
            })

    return result


@router.get("/{tenant_id}/role", response_model=RoleResponse)
async def get_my_role_in_tenant(
    tenant_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's role in a specific tenant.
    """
    # Verify user has access
    if not utr_crud.user_has_access_to_tenant(db, user.id, tenant_id):
        raise HTTPException(status_code=403, detail="No access to this tenant")

    role = utr_crud.get_user_role_in_tenant(db, user.id, tenant_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found in tenant")

    return role


@router.get("/{tenant_id}/permissions")
async def get_my_permissions_in_tenant(
    tenant_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's effective permissions in a specific tenant.
    """
    # Verify user has access
    if not utr_crud.user_has_access_to_tenant(db, user.id, tenant_id):
        raise HTTPException(status_code=403, detail="No access to this tenant")

    permissions = utr_crud.get_user_permissions_in_tenant(db, user.id, tenant_id)
    return {"tenant_id": tenant_id, "permissions": permissions}


# Admin endpoints for managing user access to tenants
@router.post("/users/{user_id}/tenants")
async def add_user_to_tenant(
    user_id: str,
    data: AddUserToTenantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a user to a tenant with a specific role.
    Requires admin permissions in the target tenant.
    """
    # Check if current user has admin rights in the target tenant
    current_role = utr_crud.get_user_role_in_tenant(db, current_user.id, data.tenant_id)
    if not current_role or current_role.name != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required to add users to tenant"
        )

    # Verify tenant exists
    tenant = tenant_crud.get_tenant_by_id(db, data.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Add user to tenant
    utr = utr_crud.add_user_to_tenant(
        db=db,
        user_id=user_id,
        tenant_id=data.tenant_id,
        role_id=data.role_id,
        expires_at=data.expires_at
    )

    return {"message": "User added to tenant successfully", "id": utr.id}


@router.put("/users/{user_id}/tenants/{tenant_id}/role")
async def update_user_role_in_tenant(
    user_id: str,
    tenant_id: str,
    data: UpdateRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a user's role in a specific tenant.
    Requires admin permissions in the tenant.
    """
    # Check if current user has admin rights
    current_role = utr_crud.get_user_role_in_tenant(db, current_user.id, tenant_id)
    if not current_role or current_role.name != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required to update user roles"
        )

    # Update role
    utr = utr_crud.update_user_role_in_tenant(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
        new_role_id=data.role_id
    )

    if not utr:
        raise HTTPException(status_code=404, detail="User-tenant association not found")

    return {"message": "User role updated successfully"}


@router.delete("/users/{user_id}/tenants/{tenant_id}")
async def remove_user_from_tenant(
    user_id: str,
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a user's access to a tenant.
    Requires admin permissions in the tenant.
    """
    # Check if current user has admin rights
    current_role = utr_crud.get_user_role_in_tenant(db, current_user.id, tenant_id)
    if not current_role or current_role.name != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required to remove users from tenant"
        )

    # Don't allow removing self from default tenant
    if user_id == current_user.id and tenant_id == current_user.default_tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove yourself from your default tenant"
        )

    # Remove user from tenant
    success = utr_crud.remove_user_from_tenant(db, user_id, tenant_id)

    if not success:
        raise HTTPException(status_code=404, detail="User-tenant association not found")

    return {"message": "User removed from tenant successfully"}


@router.post("/users/{user_id}/tenants/{tenant_id}/deactivate")
async def deactivate_user_in_tenant(
    user_id: str,
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user's access to a tenant without deleting the association.
    Requires admin permissions in the tenant.
    """
    # Check if current user has admin rights
    current_role = utr_crud.get_user_role_in_tenant(db, current_user.id, tenant_id)
    if not current_role or current_role.name != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required to deactivate users"
        )

    # Deactivate user
    success = utr_crud.deactivate_user_in_tenant(db, user_id, tenant_id)

    if not success:
        raise HTTPException(status_code=404, detail="User-tenant association not found")

    return {"message": "User deactivated in tenant successfully"}


@router.get("/{tenant_id}/users")
async def get_tenant_users(
    tenant_id: str,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users who have access to a specific tenant.
    Requires at least viewer access to the tenant.
    """
    # Verify current user has access to this tenant
    if not utr_crud.user_has_access_to_tenant(db, current_user.id, tenant_id):
        raise HTTPException(status_code=403, detail="No access to this tenant")

    users = utr_crud.get_tenant_users(db, tenant_id, include_inactive)

    result = []
    for user in users:
        role = utr_crud.get_user_role_in_tenant(db, user.id, tenant_id)
        utr = utr_crud.get_user_tenant_role(db, user.id, tenant_id)

        if role and utr:
            result.append({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "name": user.name,
                "role": {"id": role.id, "name": role.name},
                "is_active": utr.is_active,
                "created_at": utr.created_at
            })

    return result


# Tenant CRUD endpoints
@router.get("", response_model=List[TenantResponse])
async def list_all_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all tenants in the system.
    """
    tenants = tenant_crud.get_all_tenants(db, skip=skip, limit=limit)
    return tenants


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific tenant by ID"""
    tenant = tenant_crud.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


class CreateTenantRequest(BaseModel):
    name: str
    subdomain: str | None = None


@router.post("", response_model=TenantResponse)
async def create_tenant(
    data: CreateTenantRequest,
    db: Session = Depends(get_db)
):
    """Create a new tenant"""
    # Check if subdomain already exists
    if data.subdomain:
        existing = tenant_crud.get_tenant_by_subdomain(db, data.subdomain)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Subdomain '{data.subdomain}' is already taken"
            )

    tenant = tenant_crud.create_tenant(
        db=db,
        name=data.name,
        subdomain=data.subdomain
    )
    return tenant


class UpdateTenantRequest(BaseModel):
    name: str | None = None
    subdomain: str | None = None
    is_active: bool | None = None


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    data: UpdateTenantRequest,
    db: Session = Depends(get_db)
):
    """Update a tenant"""
    tenant = tenant_crud.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check if new subdomain conflicts
    if data.subdomain and data.subdomain != tenant.subdomain:
        existing = tenant_crud.get_tenant_by_subdomain(db, data.subdomain)
        if existing and existing.id != tenant_id:
            raise HTTPException(
                status_code=400,
                detail=f"Subdomain '{data.subdomain}' is already taken"
            )

    # Update fields
    if data.name:
        tenant.name = data.name
    if data.subdomain is not None:
        tenant.subdomain = data.subdomain
    if data.is_active is not None:
        tenant.is_active = data.is_active

    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/{tenant_id}/deactivate")
async def deactivate_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Deactivate a tenant"""
    tenant = tenant_crud.deactivate_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deactivated successfully"}


@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Activate a tenant"""
    tenant = tenant_crud.activate_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant activated successfully"}

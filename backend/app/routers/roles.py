"""
Roles management router for CRUD operations on global roles.
Roles are global entities (superuser, admin, edit, read) that can be assigned to users in different spaces.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.crud import roles as role_crud

router = APIRouter(prefix="/api/roles", tags=["roles"])


class RoleResponse(BaseModel):
    id: str
    name: str
    permissions: Dict[str, Any]
    created_at: str

    class Config:
        from_attributes = True


class CreateRole(BaseModel):
    name: str
    permissions: Dict[str, Any] = {}


class UpdateRole(BaseModel):
    name: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[RoleResponse])
async def list_roles(db: Session = Depends(get_db)):
    """
    List all global roles.
    Returns all available roles that can be assigned to users in spaces.
    """
    roles = role_crud.get_all_roles(db)

    return [
        RoleResponse(
            id=role.id,
            name=role.name,
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
        permissions=role.permissions,
        created_at=role.created_at.isoformat()
    )


@router.post("", response_model=RoleResponse)
async def create_role(role_data: CreateRole, db: Session = Depends(get_db)):
    """
    Create a new global role.
    Note: Only superusers should be allowed to create roles.
    """
    # Check if role with same name already exists (globally unique)
    existing = role_crud.get_role_by_name(db, role_data.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Role '{role_data.name}' already exists"
        )

    role = role_crud.create_role(
        db=db,
        name=role_data.name,
        permissions=role_data.permissions
    )

    return RoleResponse(
        id=role.id,
        name=role.name,
        permissions=role.permissions,
        created_at=role.created_at.isoformat()
    )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: UpdateRole,
    db: Session = Depends(get_db)
):
    """
    Update a global role.
    Note: Only superusers should be allowed to update roles.
    """
    role = role_crud.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if new name conflicts with existing role (globally unique)
    if role_data.name and role_data.name != role.name:
        existing = role_crud.get_role_by_name(db, role_data.name)
        if existing and existing.id != role_id:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{role_data.name}' already exists"
            )

    # Update role
    updated_role = role_crud.update_role(
        db=db,
        role_id=role_id,
        name=role_data.name,
        permissions=role_data.permissions
    )

    return RoleResponse(
        id=updated_role.id,
        name=updated_role.name,
        permissions=updated_role.permissions,
        created_at=updated_role.created_at.isoformat()
    )


@router.delete("/{role_id}")
async def delete_role(role_id: str, db: Session = Depends(get_db)):
    """
    Delete a global role.
    Note: This will fail if there are users currently assigned to this role.
    Only superusers should be allowed to delete roles.
    """
    from app.models.db_models import UserSpaceRole

    role = role_crud.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if any users have this role in any space
    users_with_role = db.query(UserSpaceRole).filter(
        UserSpaceRole.role_id == role_id
    ).count()

    if users_with_role > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role '{role.name}'. {users_with_role} user(s) are currently assigned to this role across all spaces. Please reassign them first."
        )

    role_crud.delete_role(db, role_id)

    return {"message": f"Role '{role.name}' deleted successfully"}

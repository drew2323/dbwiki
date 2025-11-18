"""
Space management API endpoints for CMS.
Allows users to manage their space access and switch between spaces.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.crud import user_space_roles as usr_crud
from app.crud import spaces as space_crud
from app.models.db_models import User, Space, Role

router = APIRouter(prefix="/api/spaces", tags=["spaces"])


# Pydantic models for request/response
class SpaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    name: str
    description: str | None
    visibility: str
    home_page_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    permissions: dict


class UserSpaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    space: SpaceResponse
    role: RoleResponse
    is_active: bool
    created_at: datetime
    expires_at: datetime | None


class AddUserToSpaceRequest(BaseModel):
    space_id: str
    role_id: str
    expires_at: datetime | None = None


class UpdateRoleRequest(BaseModel):
    role_id: str


# Endpoints
@router.get("/me", response_model=List[UserSpaceResponse])
async def get_my_spaces(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all spaces the current user has access to with their roles.
    """
    spaces = usr_crud.get_user_spaces(db, user.id)

    result = []
    for space in spaces:
        role = usr_crud.get_user_role_in_space(db, user.id, space.id)
        usr = usr_crud.get_user_space_role(db, user.id, space.id)

        if role and usr:
            result.append({
                "space": space,
                "role": role,
                "is_active": usr.is_active,
                "created_at": usr.created_at,
                "expires_at": usr.expires_at
            })

    return result


@router.get("/{space_id}/role", response_model=RoleResponse)
async def get_my_role_in_space(
    space_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's role in a specific space.
    """
    # Verify user has access
    if not usr_crud.user_has_access_to_space(db, user.id, space_id):
        raise HTTPException(status_code=403, detail="No access to this space")

    role = usr_crud.get_user_role_in_space(db, user.id, space_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found in space")

    return role


@router.get("/{space_id}/permissions")
async def get_my_permissions_in_space(
    space_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's effective permissions in a specific space.
    """
    # Verify user has access
    if not usr_crud.user_has_access_to_space(db, user.id, space_id):
        raise HTTPException(status_code=403, detail="No access to this space")

    permissions = usr_crud.get_user_permissions_in_space(db, user.id, space_id)
    return {"space_id": space_id, "permissions": permissions}


# Admin endpoints for managing user access to spaces
@router.post("/users/{user_id}/spaces")
async def add_user_to_space(
    user_id: str,
    data: AddUserToSpaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a user to a space with a specific role.
    Requires admin permissions in the target space (or superuser).
    """
    # Superusers can add users to any space
    if not current_user.is_superuser:
        # Check if current user has admin rights in the target space
        current_role = usr_crud.get_user_role_in_space(db, current_user.id, data.space_id)
        if not current_role or current_role.name != "Admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to add users to space"
            )

    # Verify space exists
    space = space_crud.get_space_by_id(db, data.space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Add user to space
    usr = usr_crud.add_user_to_space(
        db=db,
        user_id=user_id,
        space_id=data.space_id,
        role_id=data.role_id,
        expires_at=data.expires_at
    )

    return {"message": "User added to space successfully", "id": usr.id}


@router.put("/users/{user_id}/spaces/{space_id}/role")
async def update_user_role_in_space(
    user_id: str,
    space_id: str,
    data: UpdateRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a user's role in a specific space.
    Requires admin permissions in the space (or superuser).
    """
    # Superusers can update roles in any space
    if not current_user.is_superuser:
        # Check if current user has admin rights
        current_role = usr_crud.get_user_role_in_space(db, current_user.id, space_id)
        if not current_role or current_role.name != "Admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to update user roles"
            )

    # Update role
    usr = usr_crud.update_user_role_in_space(
        db=db,
        user_id=user_id,
        space_id=space_id,
        new_role_id=data.role_id
    )

    if not usr:
        raise HTTPException(status_code=404, detail="User-space association not found")

    return {"message": "User role updated successfully"}


@router.delete("/users/{user_id}/spaces/{space_id}")
async def remove_user_from_space(
    user_id: str,
    space_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a user's access to a space.
    Requires admin permissions in the space (or superuser).
    """
    # Superusers can remove users from any space
    if not current_user.is_superuser:
        # Check if current user has admin rights
        current_role = usr_crud.get_user_role_in_space(db, current_user.id, space_id)
        if not current_role or current_role.name != "Admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to remove users from space"
            )

    # Remove user from space
    success = usr_crud.remove_user_from_space(db, user_id, space_id)

    if not success:
        raise HTTPException(status_code=404, detail="User-space association not found")

    return {"message": "User removed from space successfully"}


@router.post("/users/{user_id}/spaces/{space_id}/deactivate")
async def deactivate_user_in_space(
    user_id: str,
    space_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user's access to a space without deleting the association.
    Requires admin permissions in the space (or superuser).
    """
    # Superusers can deactivate users in any space
    if not current_user.is_superuser:
        # Check if current user has admin rights
        current_role = usr_crud.get_user_role_in_space(db, current_user.id, space_id)
        if not current_role or current_role.name != "Admin":
            raise HTTPException(
                status_code=403,
                detail="Admin role required to deactivate users"
            )

    # Deactivate user
    success = usr_crud.deactivate_user_in_space(db, user_id, space_id)

    if not success:
        raise HTTPException(status_code=404, detail="User-space association not found")

    return {"message": "User deactivated in space successfully"}


@router.get("/{space_id}/users")
async def get_space_users(
    space_id: str,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users who have access to a specific space.
    Requires at least viewer access to the space.
    """
    # Verify current user has access to this space
    if not usr_crud.user_has_access_to_space(db, current_user.id, space_id):
        raise HTTPException(status_code=403, detail="No access to this space")

    users = usr_crud.get_space_users(db, space_id, include_inactive)

    result = []
    for user in users:
        role = usr_crud.get_user_role_in_space(db, user.id, space_id)
        usr = usr_crud.get_user_space_role(db, user.id, space_id)

        if role and usr:
            result.append({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "name": user.name,
                "role": {"id": role.id, "name": role.name},
                "is_active": usr.is_active,
                "created_at": usr.created_at
            })

    return result


# Space CRUD endpoints
@router.get("", response_model=List[SpaceResponse])
async def list_all_spaces(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all spaces in the system.
    For superusers: Returns all spaces.
    For regular users: Returns only spaces they are members of.
    """
    if current_user.is_superuser:
        # Superusers see all spaces
        spaces = space_crud.get_all_spaces(db, skip=skip, limit=limit)
    else:
        # Regular users only see spaces they have access to
        user_spaces = usr_crud.get_user_spaces(db, current_user.id)
        spaces = user_spaces

    return spaces


@router.get("/admin/spaces", response_model=List[SpaceResponse])
async def list_admin_spaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get spaces where current user has admin rights.
    For superusers: Returns all spaces (superusers have implicit admin rights everywhere).
    For admins: Returns only spaces where they have the 'admin' role.
    """
    if current_user.is_superuser:
        # Superusers have admin rights to all spaces
        return space_crud.get_all_spaces(db)

    # Get all spaces where user has admin role
    admin_spaces = []
    user_spaces = usr_crud.get_user_spaces(db, current_user.id)

    for space in user_spaces:
        role = usr_crud.get_user_role_in_space(db, current_user.id, space.id)
        if role and role.name.lower() == "admin":
            admin_spaces.append(space)

    return admin_spaces


@router.get("/{space_id}", response_model=SpaceResponse)
async def get_space(
    space_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific space by ID"""
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


class CreateSpaceRequest(BaseModel):
    key: str
    name: str
    description: str | None = None
    visibility: str = 'private'


@router.post("", response_model=SpaceResponse)
async def create_space(
    data: CreateSpaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new space"""
    # Check if key already exists
    existing = space_crud.get_space_by_key(db, data.key)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Key '{data.key}' is already taken"
        )

    space = space_crud.create_space(
        db=db,
        key=data.key,
        name=data.name,
        description=data.description,
        visibility=data.visibility,
        created_by=current_user.id
    )
    return space


class UpdateSpaceRequest(BaseModel):
    key: str | None = None
    name: str | None = None
    description: str | None = None
    visibility: str | None = None
    home_page_id: str | None = None


@router.put("/{space_id}", response_model=SpaceResponse)
async def update_space(
    space_id: str,
    data: UpdateSpaceRequest,
    db: Session = Depends(get_db)
):
    """Update a space"""
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Check if new key conflicts
    if data.key and data.key != space.key:
        existing = space_crud.get_space_by_key(db, data.key)
        if existing and existing.id != space_id:
            raise HTTPException(
                status_code=400,
                detail=f"Key '{data.key}' is already taken"
            )

    updated_space = space_crud.update_space(
        db=db,
        space_id=space_id,
        key=data.key,
        name=data.name,
        description=data.description,
        visibility=data.visibility,
        home_page_id=data.home_page_id
    )

    return updated_space


@router.delete("/{space_id}")
async def delete_space(
    space_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a space (hard delete)"""
    # Verify space exists and user is creator or admin
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Check if user is creator or admin in the space
    is_creator = space.created_by == current_user.id
    current_role = usr_crud.get_user_role_in_space(db, current_user.id, space_id)
    is_admin = current_role and current_role.name == "Admin"

    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Only space creator or admin can delete the space"
        )

    success = space_crud.delete_space(db, space_id)
    if not success:
        raise HTTPException(status_code=404, detail="Space not found")

    return {"message": "Space deleted successfully"}

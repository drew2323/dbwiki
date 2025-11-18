"""
User management router for CRUD operations on users.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.crud import users as user_crud
from app.models.user import UserResponse
from app.dependencies.auth import require_superuser
from app.models.db_models import User

router = APIRouter(prefix="/api/users", tags=["users"])


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


@router.get("", response_model=List[UserResponse])
async def list_users(
    space_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all users with optional filtering by space and search.
    Supports pagination.
    """
    users = user_crud.get_users(db, space_id=space_id, skip=skip, limit=limit)

    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        users = [
            u for u in users
            if search_lower in u.email.lower()
            or search_lower in u.username.lower()
            or (u.name and search_lower in u.name.lower())
        ]

    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a single user by ID"""
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user details"""
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if email/username already taken by another user
    if user_data.email and user_data.email != user.email:
        existing = user_crud.get_user_by_email(db, user_data.email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")

    if user_data.username and user_data.username != user.username:
        existing = user_crud.get_user_by_username(db, user_data.username)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken")

    # Update fields
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/activate")
async def activate_user(user_id: str, db: Session = Depends(get_db)):
    """Activate a user account"""
    user = user_crud.activate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(user_id: str, db: Session = Depends(get_db)):
    """Deactivate a user account"""
    user = user_crud.deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated successfully"}


@router.delete("/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    Permanently delete a user and all associated data.

    This will CASCADE delete:
    - All auth identities (passwords, OAuth connections)
    - All space memberships (user_space_roles)

    Note: This is a destructive operation and cannot be undone.
    Use the deactivate endpoint for soft deletion.
    """
    success = user_crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# Superuser management endpoints
@router.post("/{user_id}/superuser")
async def grant_superuser(
    user_id: str,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Grant superuser status to a user.
    Only superusers can grant superuser status.
    """
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_superuser:
        raise HTTPException(status_code=400, detail="User is already a superuser")

    user.is_superuser = True
    db.commit()
    db.refresh(user)

    return {
        "message": f"User {user.username} is now a superuser",
        "user_id": user.id,
        "is_superuser": user.is_superuser
    }


@router.delete("/{user_id}/superuser")
async def revoke_superuser(
    user_id: str,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Revoke superuser status from a user.
    Only superusers can revoke superuser status.
    """
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_superuser:
        raise HTTPException(status_code=400, detail="User is not a superuser")

    # Prevent removing superuser status from yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke your own superuser status"
        )

    user.is_superuser = False
    db.commit()
    db.refresh(user)

    return {
        "message": f"Superuser status revoked from {user.username}",
        "user_id": user.id,
        "is_superuser": user.is_superuser
    }

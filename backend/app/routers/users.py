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

router = APIRouter(prefix="/api/users", tags=["users"])


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


@router.get("", response_model=List[UserResponse])
async def list_users(
    tenant_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all users with optional filtering by tenant and search.
    Supports pagination.
    """
    users = user_crud.get_users(db, tenant_id=tenant_id, skip=skip, limit=limit)

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
    Delete a user (soft delete by deactivating).
    Note: This performs a soft delete by deactivating the user.
    Hard deletes should be done carefully due to foreign key constraints.
    """
    user = user_crud.deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

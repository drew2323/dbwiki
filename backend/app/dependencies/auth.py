from fastapi import Request, HTTPException, Depends, Header
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.utils.auth import verify_token
from app.crud import users as user_crud
from app.crud import user_space_roles as usr_crud
from app.models.db_models import User, Role
from app.database import get_db


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Dependency to get current authenticated user from cookie.
    Raises 401 if not authenticated.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return user


async def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Does not raise an exception.
    """
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


async def get_current_space_id(
    request: Request,
    x_space_id: Optional[str] = Header(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """
    Get the current space context from header.
    Header format: X-Space-Id: <space_id>
    Raises 400 if no space context provided.
    Superusers automatically have access to all spaces.
    """
    if not x_space_id:
        raise HTTPException(
            status_code=400,
            detail="X-Space-Id header is required"
        )

    # Superusers have implicit access to all spaces
    if user.is_superuser:
        return x_space_id

    # Verify user has access to this space
    if not usr_crud.user_has_access_to_space(db, user.id, x_space_id):
        raise HTTPException(
            status_code=403,
            detail=f"User does not have access to space {x_space_id}"
        )

    return x_space_id


async def get_user_with_space(
    user: User = Depends(get_current_user),
    space_id: str = Depends(get_current_space_id),
    db: Session = Depends(get_db)
) -> Tuple[User, str]:
    """
    Get both the current user and space context.
    Returns: (user, space_id)
    """
    return user, space_id


async def get_user_role_in_space(
    user: User = Depends(get_current_user),
    space_id: str = Depends(get_current_space_id),
    db: Session = Depends(get_db)
) -> Role:
    """
    Get the user's role in the current space context.
    """
    role = usr_crud.get_user_role_in_space(db, user.id, space_id)
    if not role:
        raise HTTPException(
            status_code=403,
            detail=f"User has no role in space {space_id}"
        )
    return role


def require_role_in_space(required_role: str):
    """
    Dependency factory to require specific role in current space context.
    Usage: user = Depends(require_role_in_space("Admin"))
    Superusers automatically pass all role checks.
    """
    async def role_checker(
        user: User = Depends(get_current_user),
        space_id: str = Depends(get_current_space_id),
        db: Session = Depends(get_db)
    ) -> User:
        # Superusers bypass all role checks
        if user.is_superuser:
            return user

        role = usr_crud.get_user_role_in_space(db, user.id, space_id)
        if not role or role.name != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required in current space"
            )
        return user
    return role_checker


def require_permission_in_space(required_permission: str):
    """
    Dependency factory to require specific permission in current space context.
    Usage: user = Depends(require_permission_in_space("content_edit"))
    Superusers automatically pass all permission checks.
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
        space_id: str = Depends(get_current_space_id),
        db: Session = Depends(get_db)
    ) -> User:
        # Superusers bypass all permission checks
        if user.is_superuser:
            return user

        permissions = usr_crud.get_user_permissions_in_space(db, user.id, space_id)
        if not permissions.get(required_permission, False):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{required_permission}' required in current space"
            )
        return user
    return permission_checker


async def require_superuser(user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require superuser access.
    Usage: user = Depends(require_superuser)
    """
    if not user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Superuser access required"
        )
    return user

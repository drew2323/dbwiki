from fastapi import Request, HTTPException, Depends, Header
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.utils.auth import verify_token
from app.crud import users as user_crud
from app.crud import user_tenant_roles as utr_crud
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


async def get_current_tenant_id(
    request: Request,
    x_tenant_id: Optional[str] = Header(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """
    Get the current tenant context from header or use user's default tenant.
    Header format: X-Tenant-Id: <tenant_id>
    """
    tenant_id = x_tenant_id or user.default_tenant_id

    # Verify user has access to this tenant
    if not utr_crud.user_has_access_to_tenant(db, user.id, tenant_id):
        raise HTTPException(
            status_code=403,
            detail=f"User does not have access to tenant {tenant_id}"
        )

    return tenant_id


async def get_user_with_tenant(
    user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
) -> Tuple[User, str]:
    """
    Get both the current user and tenant context.
    Returns: (user, tenant_id)
    """
    return user, tenant_id


async def get_user_role_in_tenant(
    user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
) -> Role:
    """
    Get the user's role in the current tenant context.
    """
    role = utr_crud.get_user_role_in_tenant(db, user.id, tenant_id)
    if not role:
        raise HTTPException(
            status_code=403,
            detail=f"User has no role in tenant {tenant_id}"
        )
    return role


def require_role_in_tenant(required_role: str):
    """
    Dependency factory to require specific role in current tenant context.
    Usage: user = Depends(require_role_in_tenant("Admin"))
    """
    async def role_checker(
        user: User = Depends(get_current_user),
        tenant_id: str = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
    ) -> User:
        role = utr_crud.get_user_role_in_tenant(db, user.id, tenant_id)
        if not role or role.name != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required in current tenant"
            )
        return user
    return role_checker


def require_permission_in_tenant(required_permission: str):
    """
    Dependency factory to require specific permission in current tenant context.
    Usage: user = Depends(require_permission_in_tenant("content_edit"))
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
        tenant_id: str = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
    ) -> User:
        permissions = utr_crud.get_user_permissions_in_tenant(db, user.id, tenant_id)
        if not permissions.get(required_permission, False):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{required_permission}' required in current tenant"
            )
        return user
    return permission_checker


# Legacy: Keep for backward compatibility with default tenant
def require_role(required_role: str):
    """
    Dependency factory to require specific role in default tenant.
    DEPRECATED: Use require_role_in_tenant for multi-tenant support.
    Usage: user = Depends(require_role("Admin"))
    """
    async def role_checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        role = utr_crud.get_user_role_in_tenant(db, user.id, user.default_tenant_id)
        if not role or role.name != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required"
            )
        return user
    return role_checker


def require_permission(required_permission: str):
    """
    Dependency factory to require specific permission in default tenant.
    DEPRECATED: Use require_permission_in_tenant for multi-tenant support.
    Usage: user = Depends(require_permission("content_edit"))
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        permissions = utr_crud.get_user_permissions_in_tenant(db, user.id, user.default_tenant_id)
        if not permissions.get(required_permission, False):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{required_permission}' required"
            )
        return user
    return permission_checker

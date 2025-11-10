from fastapi import Request, HTTPException, Depends
from typing import Optional
from app.utils.auth import verify_token
from app.utils.mock_users import get_user_by_id
from app.models.user import User


async def get_current_user(request: Request) -> User:
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

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Does not raise an exception.
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

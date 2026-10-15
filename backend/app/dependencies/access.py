"""
Space-level access checks for CMS endpoints.

Read access: public spaces are readable by anyone (including anonymous
visitors); private spaces need superuser flag, active membership or authorship.
Write access always needs an authenticated user with one of the latter.
"""
from typing import Optional
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user_optional
from app.models.db_models import Space, User
from app.crud import spaces as space_crud
from app.crud import user_space_roles as usr_crud


def is_public_space(space: Space) -> bool:
    return bool(space.is_public) or space.visibility == "public"


def user_is_space_member(db: Session, user: User, space: Space) -> bool:
    if user.is_superuser or space.created_by == user.id:
        return True
    return usr_crud.user_has_access_to_space(db, user.id, space.id)


WRITE_ROLES = {"superuser", "admin", "edit"}


def user_can_write_space(db: Session, user: User, space: Space) -> bool:
    """Superusers, the space creator and members with an admin/edit role may modify content."""
    if user.is_superuser or space.created_by == user.id:
        return True
    role = usr_crud.get_user_role_in_space(db, user.id, space.id)
    return bool(role and role.name.lower() in WRITE_ROLES)


def require_space_read(db: Session, space_id: str, user: Optional[User]) -> Space:
    """Return the space if `user` (possibly anonymous) may read it."""
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    if is_public_space(space):
        return space
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user_is_space_member(db, user, space):
        raise HTTPException(status_code=403, detail="No access to this space")
    return space


def require_space_write(db: Session, space_id: str, user: User) -> Space:
    """Return the space if `user` may modify its content."""
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    if not user_can_write_space(db, user, space):
        raise HTTPException(status_code=403, detail="No write access to this space")
    return space


def readable_space_ids(db: Session, user: Optional[User]) -> Optional[list]:
    """Space ids visible to `user`, or None when every space is visible (superuser)."""
    if user is not None and user.is_superuser:
        return None
    ids = {s.id for s in db.query(Space).filter(
        (Space.is_public == True) | (Space.visibility == "public")  # noqa: E712
    ).all()}
    if user is not None:
        ids |= {s.id for s in usr_crud.get_user_spaces(db, user.id)}
        ids |= {s.id for s in db.query(Space).filter(Space.created_by == user.id).all()}
    return list(ids)


# FastAPI dependency alias so routers read nicely
OptionalUser = Depends(get_current_user_optional)

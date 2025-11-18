from sqlalchemy.orm import Session
from app.models.db_models import Space
from typing import Optional, List
import uuid

def get_space_by_id(db: Session, space_id: str) -> Optional[Space]:
    return db.query(Space).filter(Space.id == space_id).first()

def get_space_by_key(db: Session, key: str) -> Optional[Space]:
    """Get space by its URL-safe key"""
    return db.query(Space).filter(Space.key == key).first()

def get_all_spaces(db: Session, skip: int = 0, limit: int = 100) -> List[Space]:
    return db.query(Space).offset(skip).limit(limit).all()

def create_space(
    db: Session,
    key: str,
    name: str,
    created_by: str,
    description: Optional[str] = None,
    visibility: str = 'private'
) -> Space:
    space = Space(
        id=str(uuid.uuid4()),
        key=key,
        name=name,
        description=description,
        visibility=visibility,
        created_by=created_by
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space

def update_space(
    db: Session,
    space_id: str,
    key: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[str] = None,
    home_page_id: Optional[str] = None
) -> Optional[Space]:
    space = db.query(Space).filter(Space.id == space_id).first()
    if space:
        if key is not None:
            space.key = key
        if name is not None:
            space.name = name
        if description is not None:
            space.description = description
        if visibility is not None:
            space.visibility = visibility
        if home_page_id is not None:
            space.home_page_id = home_page_id
        db.commit()
        db.refresh(space)
    return space

def delete_space(db: Session, space_id: str) -> bool:
    """Delete a space (hard delete)"""
    space = db.query(Space).filter(Space.id == space_id).first()
    if space:
        db.delete(space)
        db.commit()
        return True
    return False

"""
CRUD operations for page versions
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.db_models import PageVersion, Page
from typing import Optional, List, Dict, Any
import uuid


def get_version_by_id(db: Session, version_id: str) -> Optional[PageVersion]:
    """Get version by ID"""
    return db.query(PageVersion).filter(PageVersion.id == version_id).first()


def get_versions_by_page(
    db: Session,
    page_id: str,
    skip: int = 0,
    limit: int = 50
) -> List[PageVersion]:
    """Get all versions for a page, newest first"""
    return db.query(PageVersion).filter(
        PageVersion.page_id == page_id
    ).order_by(
        desc(PageVersion.version_number)
    ).offset(skip).limit(limit).all()


def get_latest_version(db: Session, page_id: str) -> Optional[PageVersion]:
    """Get the latest published version for a page"""
    return db.query(PageVersion).filter(
        PageVersion.page_id == page_id
    ).order_by(
        desc(PageVersion.version_number)
    ).first()


def get_version_by_number(db: Session, page_id: str, version_number: int) -> Optional[PageVersion]:
    """Get specific version by number"""
    return db.query(PageVersion).filter(
        PageVersion.page_id == page_id,
        PageVersion.version_number == version_number
    ).first()


def create_version(
    db: Session,
    page_id: str,
    title: str,
    content_json: Dict[str, Any],
    content_text: str,
    author_id: str,
    notes: Optional[str] = None
) -> PageVersion:
    """
    Create a new version for a page.
    Automatically increments version number.
    """
    # Get the latest version number
    latest = get_latest_version(db, page_id)
    version_number = (latest.version_number + 1) if latest else 1

    version = PageVersion(
        id=str(uuid.uuid4()),
        page_id=page_id,
        version_number=version_number,
        title=title,
        content_json=content_json,
        content_text=content_text,
        author_id=author_id,
        notes=notes
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def publish_draft(
    db: Session,
    page_id: str,
    author_id: str,
    notes: Optional[str] = None
) -> Optional[PageVersion]:
    """
    Publish the current draft by creating a new version.
    Copies draft content to a new version record.
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page or not page.draft_json:
        return None

    version = create_version(
        db=db,
        page_id=page_id,
        title=page.title,
        content_json=page.draft_json,
        content_text=page.draft_text or "",
        author_id=author_id,
        notes=notes
    )

    # Update page's updated_at timestamp
    from sqlalchemy import func
    page.updated_at = func.now()
    db.commit()

    return version


def restore_version_to_draft(
    db: Session,
    page_id: str,
    version_id: str
) -> Optional[Page]:
    """
    Restore a version's content to the page's draft.
    Does not create a new version - just updates the draft.
    """
    version = get_version_by_id(db, version_id)
    if not version or version.page_id != page_id:
        return None

    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return None

    # Copy version content to draft
    page.draft_json = version.content_json
    page.draft_text = version.content_text
    page.title = version.title

    # Generate new ETag
    from app.crud.pages import generate_etag
    page.draft_etag = generate_etag(version.content_json)

    from sqlalchemy import func
    page.updated_at = func.now()

    db.commit()
    db.refresh(page)
    return page


def delete_version(db: Session, version_id: str) -> bool:
    """Delete a version (hard delete - use with caution!)"""
    version = db.query(PageVersion).filter(PageVersion.id == version_id).first()
    if not version:
        return False

    db.delete(version)
    db.commit()
    return True


def count_versions(db: Session, page_id: str) -> int:
    """Get total count of versions for a page"""
    return db.query(PageVersion).filter(PageVersion.page_id == page_id).count()
